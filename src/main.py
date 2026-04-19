"""
Päämoduuli - GPU-kiihdytetty äänenlaatu-analysaattori
"""

import os
import sys
import yaml
import torch
import librosa
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
from datetime import datetime
import base64
import json

# Import custom modules
from src.dsp_analyzer import DSPAnalyzer
from src.gpu_features import GPUFeatureExtractor, AudioQualityEmbeddingNet
from src.ai_model import AudioQualityAssessmentModel, RecommendationEngine, format_analysis_report
from src.visualizations import create_analysis_visualizations
from src.llm_explainer import LLMExplainer, check_ollama_status


class AudioQualityAnalyzer:
    """
    Pääluokka joka koordinoi koko analyysin
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize analyzer with configuration"""
        # Load config
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Setup device
        self.device = self._setup_device()
        
        # Initialize components
        print("Initializing audio quality analyzer...")
        
        # DSP Analyzer
        self.dsp_analyzer = DSPAnalyzer(
            sample_rate=self.config['dsp']['sample_rate'],
            config=self.config['dsp']
        )
        
        # GPU Feature Extractor
        self.feature_extractor = GPUFeatureExtractor(
            sample_rate=self.config['dsp']['sample_rate'],
            n_fft=self.config['dsp']['fft_size'],
            hop_length=self.config['dsp']['hop_length'],
            n_mels=self.config['dsp']['n_mels'],
            device=self.device
        )
        
        # AI Model
        self.ai_model = AudioQualityAssessmentModel(
            embedding_dim=self.config['ai_model']['embedding_dim'],
            num_heads=self.config['ai_model']['num_heads'],
            num_layers=self.config['ai_model']['num_layers'],
            dropout=self.config['ai_model']['dropout']
        ).to(self.device)
        
        # Recommendation Engine
        self.recommendation_engine = RecommendationEngine()
        
        # LLM Explainer (optional - fails gracefully if Ollama not available)
        try:
            # Check if LLM is enabled in config
            llm_enabled_config = self.config.get('llm', {}).get('enabled', True)
            if not llm_enabled_config:
                raise ValueError("LLM disabled in config")
            
            # Use environment variable if set, otherwise use config
            ollama_url = os.environ.get('OLLAMA_URL', 
                                        self.config.get('llm', {}).get('ollama_url', 'http://localhost:11434'))
            llm_model = self.config.get('llm', {}).get('model', 'mistral')
            llm_timeout = self.config.get('llm', {}).get('timeout', 180)
            self.llm_explainer = LLMExplainer(
                ollama_url=ollama_url, 
                model=llm_model,
                timeout=llm_timeout
            )
            self.llm_enabled = True
            print(f"✓ LLM Explainer initialized (model: {llm_model}, url: {ollama_url}, timeout: {llm_timeout}s)")
        except Exception as e:
            self.llm_explainer = None
            self.llm_enabled = False
            print(f"⚠ LLM Explainer disabled: {e}")
        
        # 
        # Set model to evaluation mode
        self.ai_model.eval()
        
        print(f"✓ Analyzer initialized on device: {self.device}")
        print(f"✓ GPU available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✓ GPU device: {torch.cuda.get_device_name(0)}")
    
    def _setup_device(self) -> str:
        """Setup compute device (GPU or CPU)"""
        if self.config['general']['use_gpu'] and torch.cuda.is_available():
            device = 'cuda'
        else:
            device = 'cpu'
            if self.config['general']['use_gpu']:
                print("⚠ GPU requested but not available, using CPU")
        return device
    
    def analyze_file(self, filepath: str, notes: str = "") -> Dict:
        """
        Analysoi yksi äänitiedosto
        
        Args:
            filepath: Path to audio file
            notes: Optional notes about what to focus on
            
        Returns:
            Complete analysis results
        """
        print(f"\n{'='*60}")
        print(f"Analyzing: {os.path.basename(filepath)}")
        print(f"{'='*60}")
        
        # 1. Load audio
        print("Loading audio...")
        y, sr = librosa.load(filepath, sr=self.config['dsp']['sample_rate'], mono=False)
        
        # Detect if stereo
        is_stereo = y.ndim > 1 and y.shape[0] == 2
        
        print(f"  Sample rate: {sr} Hz")
        print(f"  Channels: {'Stereo' if is_stereo else 'Mono'}")
        print(f"  Duration: {len(y[0] if is_stereo else y) / sr:.2f} seconds")
        
        # 2. DSP Analysis
        print("\nRunning DSP analysis...")
        dsp_results = self.dsp_analyzer.analyze_full(y, stereo=is_stereo)
        print("  ✓ DSP analysis complete")
        
        # 3. GPU Feature Extraction
        print("\nExtracting GPU features...")
        with torch.no_grad():
            # Convert to torch tensor
            if is_stereo:
                # Take mono for feature extraction
                y_mono = librosa.to_mono(y)
            else:
                y_mono = y
            
            waveform = torch.from_numpy(y_mono).float()
            features = self.feature_extractor.extract_all_features(waveform)
            embeddings = self.feature_extractor.compute_embeddings(features)
            # Add batch dimension for AI model
            embeddings = embeddings.unsqueeze(0)
        print("  ✓ Feature extraction complete")
        
        # 4. AI Quality Assessment
        print("\nRunning AI quality assessment...")
        with torch.no_grad():
            ai_predictions = self.ai_model(embeddings)
        print("  ✓ AI assessment complete")
        
        # 5. Generate Recommendations
        print("\nGenerating recommendations...")
        recommendations = self.recommendation_engine.generate_recommendations(
            dsp_results, ai_predictions
        )
        print("  ✓ Recommendations generated")
        
        # 6. Generate LLM Explanation (if available)
        llm_explanation = None
        if self.llm_enabled and self.llm_explainer:
            print("\nGenerating LLM explanation...")
            try:
                llm_explanation = self.llm_explainer.explain_analysis(
                    dsp_results,
                    ai_predictions,
                    recommendations,
                    os.path.basename(filepath),
                    notes
                )
                if llm_explanation:
                    print("  ✓ LLM explanation generated")
                else:
                    print("  ⚠ LLM explanation failed")
            except Exception as e:
                print(f"  ⚠ LLM explanation error: {e}")
                llm_explanation = None
        

        # Compile results
        overall_score = recommendations.get('quality_summary', {}).get('overall', {}).get('score', 0)
        
        results = {
            'filename': os.path.basename(filepath),
            'filepath': filepath,
            'overall_score': overall_score,
            'metadata': {
                'sample_rate': sr,
                'is_stereo': is_stereo,
                'duration_seconds': len(y_mono) / sr,
                'analysis_date': datetime.now().isoformat()
            },
            'dsp_analysis': dsp_results,
            'gpu_features': {k: v.cpu().numpy().tolist() if isinstance(v, torch.Tensor) 
                           else v for k, v in features.items()},
            'ai_predictions': {
                'quality_scores': {k: v.cpu().item() if isinstance(v, torch.Tensor) 
                                  else v for k, v in ai_predictions['quality_scores'].items()},
                'issues': ai_predictions['issues'].cpu().numpy().tolist(),
                'recommendations': ai_predictions['recommendations'].cpu().numpy().tolist()
            },
            'recommendations': recommendations,
            'llm_explanation': llm_explanation,
            'notes': notes
        }
        
        return results
    
    def analyze_batch(self, input_folder: Optional[str] = None) -> List[Dict]:
        """
        Analysoi kaikki äänitiedostot kansiosta
        
        Args:
            input_folder: Path to folder with audio files
            
        Returns:
            List of analysis results
        """
        if input_folder is None:
            input_folder = self.config['general']['input_folder']
        
        # Find audio files
        audio_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
        audio_files = []
        
        for ext in audio_extensions:
            audio_files.extend(Path(input_folder).glob(f'*{ext}'))
        
        if not audio_files:
            print(f"⚠ No audio files found in {input_folder}")
            return []
        
        print(f"\nFound {len(audio_files)} audio files to analyze")
        
        all_results = []
        
        for i, filepath in enumerate(audio_files, 1):
            print(f"\n[{i}/{len(audio_files)}]")
            try:
                results = self.analyze_file(str(filepath))
                all_results.append(results)
            except Exception as e:
                print(f"  ✗ Error analyzing {filepath.name}: {e}")
                continue
        
        return all_results
    
    def export_results(self, results: List[Dict], output_folder: Optional[str] = None):
        """
        Vie analyysitulokset eri formaateissa
        
        Args:
            results: List of analysis results
            output_folder: Output directory
        """
        if output_folder is None:
            output_folder = self.config['general']['output_folder']
        
        os.makedirs(output_folder, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Excel report
        if self.config['reporting']['generate_excel']:
            print("\nGenerating Excel report...")
            self._export_excel(results, output_folder, timestamp)
        
        # 2. Text reports
        print("\nGenerating text reports...")
        self._export_text_reports(results, output_folder)
        
        # 3. Visualizations
        if self.config['reporting']['generate_visualizations']:
            print("\nGenerating visualizations...")
            self._export_visualizations(results, output_folder)
        
        # 4. HTML summary report
        print("\nGenerating HTML summary report...")
        self._export_html_summary(results, output_folder, timestamp)
        
        print(f"\n✓ Results exported to: {output_folder}")
    
    def _export_excel(self, results: List[Dict], output_folder: str, timestamp: str):
        """Export summary to Excel"""
        rows = []
        
        for result in results:
            row = {
                'Tiedosto': result['filename'],
                'Kokonaislaatu': result.get('overall_score', 0),
                'Kesto (s)': result['metadata']['duration_seconds'],
                'Stereo': 'Kyllä' if result['metadata']['is_stereo'] else 'Ei'
            }
            
            # Quality scores
            for aspect, data in result['recommendations']['quality_summary'].items():
                row[f'{aspect.title()} Pisteet'] = data['score']
                row[f'{aspect.title()} Arvio'] = data['rating']
            
            # Key DSP metrics
            if 'loudness' in result['dsp_analysis']:
                row['Loudness (LUFS)'] = result['dsp_analysis']['loudness'].get('integrated_loudness_lufs', 'N/A')
            
            if 'noise' in result['dsp_analysis']:
                row['SNR (dB)'] = result['dsp_analysis']['noise'].get('snr_db', 'N/A')
            
            if 'dynamic_range' in result['dsp_analysis']:
                row['Dynamic Range (dB)'] = result['dsp_analysis']['dynamic_range'].get('dynamic_range_db', 'N/A')
            
            # Issues count
            row['Ongelmat'] = len(result['recommendations'].get('issues_detected', []))
            
            # Top recommendation
            if result['recommendations'].get('priority_actions'):
                row['Tärkein ehdotus'] = result['recommendations']['priority_actions'][0].replace('_', ' ')
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        excel_path = os.path.join(output_folder, f'audio_quality_report_{timestamp}.xlsx')
        df.to_excel(excel_path, index=False)
        print(f"  ✓ Excel: {excel_path}")
    
    def _export_text_reports(self, results: List[Dict], output_folder: str):
        """Export detailed text reports for each file"""
        reports_folder = os.path.join(output_folder, 'reports')
        os.makedirs(reports_folder, exist_ok=True)
        
        for result in results:
            # Generate formatted report
            report_text = format_analysis_report(
                result['dsp_analysis'],
                result['ai_predictions'],
                result['recommendations'],
                result['filename']
            )
            
            # Add LLM explanation if available
            if result.get('llm_explanation'):
                report_text += "\n\n" + "="*80 + "\n"
                report_text += "AI-GENERATED INSIGHTS (LLM)\n"
                report_text += "="*80 + "\n\n"
                report_text += result['llm_explanation']
                report_text += "\n\n" + "="*80 + "\n"
            
            # Save to file
            report_filename = f"{Path(result['filename']).stem}_report.txt"
            report_path = os.path.join(reports_folder, report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        print(f"  ✓ Text reports: {reports_folder}")
    
    def _export_visualizations(self, results: List[Dict], output_folder: str):
        """Export visualizations"""
        viz_folder = os.path.join(output_folder, 'visualizations')
        os.makedirs(viz_folder, exist_ok=True)
        
        for result in results:
            # Load audio again for visualization
            y, sr = librosa.load(result['filepath'], 
                               sr=self.config['dsp']['sample_rate'], 
                               mono=False)
            
            # Create visualizations
            viz_path = os.path.join(viz_folder, f"{Path(result['filename']).stem}_analysis.png")
            create_analysis_visualizations(
                y, sr, 
                result['dsp_analysis'],
                result['recommendations'],
                viz_path
            )
        
        print(f"  ✓ Visualizations: {viz_folder}")
    
    def _export_html_summary(self, results: List[Dict], output_folder: str, timestamp: str):
        """Export comprehensive HTML summary report"""
        html_path = os.path.join(output_folder, f'audio_quality_summary_{timestamp}.html')
        
        # Calculate statistics
        avg_scores = {}
        for result in results:
            for aspect, data in result['recommendations']['quality_summary'].items():
                if aspect not in avg_scores:
                    avg_scores[aspect] = []
                avg_scores[aspect].append(data['score'])
        
        overall_avg = np.mean([r.get('overall_score', 0) for r in results])
        
        # Generate HTML
        html_content = f"""<!DOCTYPE html>
<html lang="fi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Äänenlaatuanalyysi - Yhteenveto</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .meta {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }}
        
        .card h3 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .section {{
            margin-bottom: 50px;
        }}
        
        .section h2 {{
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .comparison-table th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        .comparison-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        
        .comparison-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .score-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .score-excellent {{ background: #10b981; color: white; }}
        .score-good {{ background: #3b82f6; color: white; }}
        .score-fair {{ background: #f59e0b; color: white; }}
        .score-poor {{ background: #ef4444; color: white; }}
        
        .file-detail {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid #e2e8f0;
        }}
        
        .file-detail h3 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}
        
        .quality-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        
        .quality-item {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
        }}
        
        .quality-item .label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }}
        
        .quality-item .score {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .issues-list {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            border-radius: 4px;
            margin: 15px 0;
        }}
        
        .issues-list h4 {{
            color: #856404;
            margin-bottom: 10px;
        }}
        
        .issues-list ul {{
            list-style-position: inside;
            color: #856404;
        }}
        
        .recommendations {{
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 15px 20px;
            border-radius: 4px;
            margin: 15px 0;
        }}
        
        .recommendations h4 {{
            color: #0c5460;
            margin-bottom: 10px;
        }}
        
        .recommendations ul {{
            list-style-position: inside;
            color: #0c5460;
        }}
        
        .llm-insight {{
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 20px;
            border-radius: 4px;
            margin: 15px 0;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.8;
        }}
        
        .llm-insight h4 {{
            color: #0d47a1;
            margin-bottom: 15px;
            font-family: 'Segoe UI', sans-serif;
        }}
        
        .visualization {{
            margin: 20px 0;
            text-align: center;
        }}
        
        .visualization img {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎙️ Äänenlaatuanalyysi</h1>
            <div class="meta">
                <p>Analysoitu: {datetime.now().strftime('%d.%m.%Y klo %H:%M')}</p>
                <p>Tiedostoja: {len(results)} | Keskiarvolaatu: {overall_avg:.1f}/100</p>
            </div>
        </div>
        
        <div class="content">
            <!-- Summary Cards -->
            <div class="summary-cards">
                <div class="card">
                    <h3>Analysoituja tiedostoja</h3>
                    <div class="value">{len(results)}</div>
                </div>
                <div class="card">
                    <h3>Keskiarvolaatu</h3>
                    <div class="value">{overall_avg:.1f}/100</div>
                </div>
                <div class="card">
                    <h3>Paras tulos</h3>
                    <div class="value">{max([r.get('overall_score', 0) for r in results]):.1f}/100</div>
                </div>
                <div class="card">
                    <h3>Heikoin tulos</h3>
                    <div class="value">{min([r.get('overall_score', 0) for r in results]):.1f}/100</div>
                </div>
            </div>
            
            <!-- Comparison Table -->
            <div class="section">
                <h2>📊 Vertailutaulukko</h2>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Tiedosto</th>
                            <th>Kokonaislaatu</th>
                            <th>Selkeys</th>
                            <th>Kohina</th>
                            <th>Taajuus</th>
                            <th>Dynamiikka</th>
                            <th>Loudness</th>
                            <th>Ongelmat</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        # Add rows to comparison table
        for result in sorted(results, key=lambda x: x.get('overall_score', 0), reverse=True):
            overall = result.get('overall_score', 0)
            badge_class = ('score-excellent' if overall >= 80 else 
                          'score-good' if overall >= 60 else 
                          'score-fair' if overall >= 40 else 'score-poor')
            
            quality = result['recommendations']['quality_summary']
            issues_count = len(result['recommendations'].get('issues_detected', []))
            
            html_content += f"""
                        <tr>
                            <td><strong>{result['filename']}</strong></td>
                            <td><span class="score-badge {badge_class}">{overall:.1f}</span></td>
                            <td>{quality.get('clarity', {}).get('score', 0):.1f}</td>
                            <td>{quality.get('noise', {}).get('score', 0):.1f}</td>
                            <td>{quality.get('frequency', {}).get('score', 0):.1f}</td>
                            <td>{quality.get('dynamic_range', {}).get('score', 0):.1f}</td>
                            <td>{quality.get('loudness', {}).get('score', 0):.1f}</td>
                            <td>{issues_count} ⚠</td>
                        </tr>
"""
        
        html_content += """
                    </tbody>
                </table>
            </div>
            
            <!-- Individual File Details -->
            <div class="section">
                <h2>📁 Yksityiskohtaiset analyysit</h2>
"""
        
        # Add detailed section for each file
        for result in results:
            quality = result['recommendations']['quality_summary']
            overall = result.get('overall_score', 0)
            badge_class = ('score-excellent' if overall >= 80 else 
                          'score-good' if overall >= 60 else 
                          'score-fair' if overall >= 40 else 'score-poor')
            
            html_content += f"""
                <div class="file-detail">
                    <h3>🎵 {result['filename']}</h3>
                    <p><strong>Kokonaislaatu:</strong> <span class="score-badge {badge_class}">{overall:.1f}/100</span></p>
                    <p><strong>Kesto:</strong> {result['metadata']['duration_seconds']:.1f}s | 
                       <strong>Stereo:</strong> {'Kyllä' if result['metadata']['is_stereo'] else 'Ei'} | 
                       <strong>Sample rate:</strong> {result['metadata']['sample_rate']} Hz</p>
                    
                    <div class="quality-grid">
"""
            
            # Quality scores
            for aspect, data in quality.items():
                score = data.get('score', 0)
                rating = data.get('rating', 'N/A')
                html_content += f"""
                        <div class="quality-item">
                            <div class="label">{aspect.title()}</div>
                            <div class="score">{score:.1f}/100</div>
                            <div class="label">{rating}</div>
                        </div>
"""
            
            html_content += """
                    </div>
"""
            
            # Issues
            issues = result['recommendations'].get('issues_detected', [])
            if issues:
                html_content += """
                    <div class="issues-list">
                        <h4>⚠️ Havaitut ongelmat</h4>
                        <ul>
"""
                for issue in issues[:10]:  # Top 10
                    html_content += f"""
                            <li><strong>[{issue['severity'].upper()}]</strong> {issue['issue'].replace('_', ' ').title()} (Varmuus: {issue['confidence']*100:.0f}%)</li>
"""
                html_content += """
                        </ul>
                    </div>
"""
            
            # Recommendations
            actions = result['recommendations'].get('priority_actions', [])
            if actions:
                html_content += """
                    <div class="recommendations">
                        <h4>💡 Suositellut toimenpiteet</h4>
                        <ul>
"""
                for action in actions[:5]:  # Top 5
                    html_content += f"""
                            <li>{action.replace('_', ' ').title()}</li>
"""
                html_content += """
                        </ul>
                    </div>
"""
            
            # LLM Explanation
            if result.get('llm_explanation'):
                html_content += f"""
                    <div class="llm-insight">
                        <h4>🤖 AI-analyysi (LLM)</h4>
                        {result['llm_explanation']}
                    </div>
"""
            
            # Visualization
            viz_path = os.path.join('visualizations', f"{Path(result['filename']).stem}_analysis.png")
            if os.path.exists(os.path.join(output_folder, viz_path)):
                html_content += f"""
                    <div class="visualization">
                        <img src="{viz_path}" alt="Visualisointi: {result['filename']}">
                    </div>
"""
            
            html_content += """
                </div>
"""
        
        html_content += """
            </div>
        </div>
        
        <div class="footer">
            <p>🎙️ GPU-kiihdytetty äänenlaatuanalysaattori | Generoi """ + datetime.now().strftime('%d.%m.%Y %H:%M:%S') + """</p>
            <p>Teknologia: PyTorch CUDA + Ollama LLM + DSP-analyysi</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Write HTML file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"  ✓ HTML summary: {html_path}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GPU-kiihdytetty äänenlaatu-analysaattori')
    parser.add_argument('--config', default='config.yaml', help='Config file path')
    parser.add_argument('--input', help='Input audio file or folder')
    parser.add_argument('--output', help='Output folder for results')
    parser.add_argument('--single', action='store_true', help='Analyze single file')
    parser.add_argument('--notes', default='', help='Analysis notes')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = AudioQualityAnalyzer(config_path=args.config)
    
    # Run analysis
    if args.single and args.input:
        # Single file mode
        results = [analyzer.analyze_file(args.input, notes=args.notes)]
    else:
        # Batch mode
        results = analyzer.analyze_batch(input_folder=args.input)
    
    # Export results
    if results:
        analyzer.export_results(results, output_folder=args.output)
        
        # Print summary
        print("\n" + "="*60)
        print("ANALYYSI VALMIS")
        print("="*60)
        print(f"Analysoituja tiedostoja: {len(results)}")
        
        # Average quality
        avg_scores = {}
        for result in results:
            for aspect, data in result['recommendations']['quality_summary'].items():
                if aspect not in avg_scores:
                    avg_scores[aspect] = []
                avg_scores[aspect].append(data['score'])
        
        print("\nKeskimääräiset laatupisteet:")
        for aspect, scores in avg_scores.items():
            print(f"  {aspect.title():.<30} {np.mean(scores):>5.1f}/100")
    else:
        print("\n⚠ No files analyzed")


if __name__ == "__main__":
    main()
