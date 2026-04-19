"""
LLM Explain -moduuli
Generoi ihmisluettavia selityksiä analyysituloksista käyttäen paikallista LLM:ää
Tukee Ollama API:a (Mistral, Phi, LLaMA)
"""

import requests
import json
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LLMExplainer:
    """
    Generoi kontekstuaalisia selityksiä äänenlaatuanalyyseistä
    käyttäen paikallista LLM:ää (Ollama)
    """
    
    def __init__(self, 
                 ollama_url: str = "http://localhost:11434",
                 model: str = "mistral",
                 temperature: float = 0.7,
                 timeout: int = 180):
        """
        Alusta LLM explainer
        
        Args:
            ollama_url: Ollama API URL
            model: LLM-malli (mistral, phi, llama2, etc.)
            temperature: Luovuus (0.0-1.0)
            timeout: Query timeout sekunneissa
        """
        self.ollama_url = ollama_url
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.prompt_dir = Path(__file__).parent / 'prompt_templates'
        
        # Tarkista yhteys
        self._check_connection()
        
    def _check_connection(self):
        """Tarkista että Ollama on käynnissä"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [m['name'] for m in models]
                logger.info(f"Ollama connected. Available models: {available_models}")
                
                if not any(self.model in m for m in available_models):
                    logger.warning(f"Model '{self.model}' not found. Available: {available_models}")
            else:
                logger.warning("Ollama API returned non-200 status")
        except requests.exceptions.RequestException as e:
            logger.error(f"Cannot connect to Ollama at {self.ollama_url}: {e}")
            logger.info("LLM explanations will be disabled. Install Ollama: https://ollama.ai")
    
    def explain_analysis(self,
                        dsp_results: Dict,
                        ai_predictions: Dict,
                        recommendations: Dict,
                        filename: str,
                        user_notes: str = "") -> Optional[str]:
        """
        Generoi kattava selitys analyysituloksista
        
        Args:
            dsp_results: DSP-analyysin tulokset
            ai_predictions: AI-mallin ennusteet
            recommendations: Suositukset
            filename: Tiedoston nimi
            user_notes: Käyttäjän huomiot/fokusalueet
            
        Returns:
            Generoitu selitys tai None jos LLM ei saatavilla
        """
        # Rakenna konteksti
        context = self._build_context(
            dsp_results, ai_predictions, recommendations, filename, user_notes
        )
        
        # Lataa ja muotoile prompt
        prompt = self._load_and_format_prompt('comprehensive', context)
        
        # Kysy LLM:ltä
        explanation = self._query_llm(prompt)
        
        return explanation
    
    def explain_specific_issue(self,
                               issue_type: str,
                               issue_data: Dict,
                               context: Dict) -> Optional[str]:
        """
        Selitä tietty ongelma yksityiskohtaisesti
        
        Args:
            issue_type: Ongelman tyyppi (noise, clipping, compression, etc.)
            issue_data: Ongelman data
            context: Lisäkonteksti
            
        Returns:
            Yksityiskohtainen selitys
        """
        # Lataa issue-spesifinen template
        template_name = f"issue_{issue_type}"
        
        if not (self.prompt_dir / f"{template_name}.txt").exists():
            template_name = "issue_generic"
        
        full_context = {**context, **issue_data}
        prompt = self._load_and_format_prompt(template_name, full_context)
        
        return self._query_llm(prompt)
    
    def generate_improvement_plan(self,
                                 current_results: Dict,
                                 target_criteria: Dict) -> Optional[str]:
        """
        Generoi vaiheittainen parannus-suunnitelma
        
        Args:
            current_results: Nykyiset tulokset
            target_criteria: Tavoitekriteerit
            
        Returns:
            Vaiheittainen suunnitelma
        """
        context = {
            'current_scores': current_results.get('quality_summary', {}),
            'targets': target_criteria,
            'gap_analysis': self._calculate_gaps(current_results, target_criteria)
        }
        
        prompt = self._load_and_format_prompt('improvement_plan', context)
        return self._query_llm(prompt)
    
    def _build_context(self,
                      dsp_results: Dict,
                      ai_predictions: Dict,
                      recommendations: Dict,
                      filename: str,
                      user_notes: str) -> Dict:
        """Rakenna konteksti LLM:lle"""
        
        # Overall score
        overall_score = recommendations.get('quality_summary', {}).get('overall', {}).get('score', 0)
        
        # Key metrics
        key_metrics = []
        
        if 'loudness' in dsp_results:
            lufs = dsp_results['loudness'].get('integrated_loudness_lufs', 0)
            key_metrics.append(f"Loudness: {lufs:.1f} LUFS")
        
        if 'noise' in dsp_results:
            snr = dsp_results['noise'].get('snr_db', 0)
            key_metrics.append(f"SNR: {snr:.1f} dB")
        
        if 'dynamic_range' in dsp_results:
            dr = dsp_results['dynamic_range'].get('dynamic_range_db', 0)
            key_metrics.append(f"Dynamic Range: {dr:.1f} dB")
        
        # Issues
        issues = []
        for issue in recommendations.get('issues_detected', []):
            issues.append({
                'name': issue['issue'].replace('_', ' ').title(),
                'severity': issue['severity'],
                'confidence': f"{issue['confidence']*100:.0f}%"
            })
        
        # Recommendations
        top_recommendations = []
        for rec in recommendations.get('recommendations', [])[:5]:
            top_recommendations.append({
                'action': rec.get('action', '').replace('_', ' ').title(),
                'description': rec.get('description', ''),
                'priority': f"{rec.get('priority', 0)*100:.0f}%"
            })
        
        # Quality breakdown
        quality_breakdown = {}
        for aspect, data in recommendations.get('quality_summary', {}).items():
            if aspect != 'overall':
                quality_breakdown[aspect.replace('_', ' ').title()] = {
                    'score': f"{data.get('score', 0):.0f}/100",
                    'rating': data.get('rating', 'Unknown')
                }
        
        context = {
            'filename': filename,
            'overall_score': f"{overall_score:.0f}/100",
            'overall_rating': self._score_to_rating(overall_score),
            'key_metrics': '\n'.join([f"  - {m}" for m in key_metrics]),
            'quality_breakdown': self._format_quality_breakdown(quality_breakdown),
            'issues': self._format_issues(issues),
            'recommendations': self._format_recommendations(top_recommendations),
            'user_focus': user_notes if user_notes else 'General analysis',
            'improvement_potential': f"{recommendations.get('improvement_potential', 0)*100:.0f}%"
        }
        
        return context
    
    def _load_and_format_prompt(self, template_name: str, context: Dict) -> str:
        """Lataa ja muotoile prompt-template"""
        template_path = self.prompt_dir / f"{template_name}.txt"
        
        if not template_path.exists():
            logger.warning(f"Template {template_name}.txt not found, using default")
            template_path = self.prompt_dir / "comprehensive.txt"
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Format template with context
            prompt = template.format(**context)
            return prompt
            
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return self._fallback_prompt(context)
    
    def _query_llm(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Kysy LLM:ltä"""
        import time
        
        for attempt in range(max_retries):
            try:
                print(f"  🤖 LLM query (attempt {attempt + 1}/{max_retries})")
                print(f"     Model: {self.model}")
                print(f"     URL: {self.ollama_url}")
                print(f"     Timeout: {self.timeout}s")
                print(f"     Prompt length: {len(prompt)} chars")
                
                start_time = time.time()
                
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.temperature,
                            "num_predict": 800  # Max tokens
                        }
                    },
                    timeout=self.timeout  # Use configured timeout
                )
                
                elapsed = time.time() - start_time
                print(f"     Response time: {elapsed:.1f}s")
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get('response', '').strip()
                    print(f"     ✓ Success! Response length: {len(answer)} chars")
                    return answer
                else:
                    print(f"     ✗ API error: {response.status_code}")
                    logger.error(f"LLM API error: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                elapsed = time.time() - start_time
                print(f"     ⏱ Timeout after {elapsed:.1f}s (limit: {self.timeout}s)")
                logger.warning(f"LLM query timeout (attempt {attempt + 1}/{max_retries})")
            except requests.exceptions.ConnectionError as e:
                print(f"     ✗ Connection error: {e}")
                logger.error(f"Connection error to Ollama: {e}")
            except Exception as e:
                print(f"     ✗ Error: {e}")
                logger.error(f"Error querying LLM: {e}")
        
        print(f"     ✗ All retries failed")
        return None
    
    def _fallback_prompt(self, context: Dict) -> str:
        """Fallback prompt jos template ei löydy"""
        return f"""Analyze this audio quality report and provide insights:

File: {context.get('filename', 'Unknown')}
Overall Score: {context.get('overall_score', 'N/A')}

Key Metrics:
{context.get('key_metrics', 'N/A')}

Issues:
{context.get('issues', 'None detected')}

Provide:
1. Brief assessment
2. Main issues explained
3. Top 3 recommendations
"""
    
    def _format_quality_breakdown(self, breakdown: Dict) -> str:
        """Muotoile laatuerittely"""
        lines = []
        for aspect, data in breakdown.items():
            lines.append(f"  - {aspect}: {data['score']} ({data['rating']})")
        return '\n'.join(lines) if lines else "  N/A"
    
    def _format_issues(self, issues: List[Dict]) -> str:
        """Muotoile ongelmalista"""
        if not issues:
            return "  No critical issues detected"
        
        lines = []
        for issue in issues:
            lines.append(
                f"  - {issue['name']} [{issue['severity'].upper()}] "
                f"(confidence: {issue['confidence']})"
            )
        return '\n'.join(lines)
    
    def _format_recommendations(self, recommendations: List[Dict]) -> str:
        """Muotoile suositukset"""
        if not recommendations:
            return "  No specific recommendations"
        
        lines = []
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"  {i}. {rec['action']}")
            if rec.get('description'):
                lines.append(f"     → {rec['description']}")
        return '\n'.join(lines)
    
    def _score_to_rating(self, score: float) -> str:
        """Muunna pisteet arvosanaksi"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Very Poor"
    
    def _calculate_gaps(self, current: Dict, targets: Dict) -> Dict:
        """Laske erot nykyisen ja tavoitteen välillä"""
        gaps = {}
        
        current_scores = current.get('quality_summary', {})
        
        for aspect, target_score in targets.items():
            current_score = current_scores.get(aspect, {}).get('score', 0)
            gap = target_score - current_score
            gaps[aspect] = {
                'current': current_score,
                'target': target_score,
                'gap': gap,
                'status': 'achieved' if gap <= 0 else 'needs_improvement'
            }
        
        return gaps


def check_ollama_status(url: str = "http://localhost:11434") -> Dict:
    """
    Tarkista Ollama-palvelimen tila
    
    Returns:
        Status dict with available models
    """
    try:
        response = requests.get(f"{url}/api/tags", timeout=2)
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            return {
                'status': 'connected',
                'url': url,
                'models': models,
                'model_count': len(models)
            }
    except Exception as e:
        return {
            'status': 'disconnected',
            'url': url,
            'error': str(e),
            'models': []
        }


def download_model(model_name: str = "mistral", 
                   url: str = "http://localhost:11434") -> bool:
    """
    Lataa LLM-malli Ollamalla
    
    Args:
        model_name: Mallin nimi (mistral, phi, llama2, etc.)
        url: Ollama API URL
        
    Returns:
        True jos onnistui
    """
    try:
        print(f"Downloading model '{model_name}'...")
        response = requests.post(
            f"{url}/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=300
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'status' in data:
                        print(f"  {data['status']}")
            
            print(f"✓ Model '{model_name}' downloaded successfully")
            return True
        else:
            print(f"✗ Error downloading model: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    # Test LLM connection
    print("Testing LLM Explainer...")
    print("=" * 60)
    
    # Check Ollama status
    status = check_ollama_status()
    print(f"\nOllama Status: {status['status']}")
    
    if status['status'] == 'connected':
        print(f"Available models: {status['models']}")
        
        # Test explainer
        explainer = LLMExplainer()
        
        # Mock analysis results
        mock_dsp = {
            'loudness': {'integrated_loudness_lufs': -18.5},
            'noise': {'snr_db': 32.0},
            'dynamic_range': {'dynamic_range_db': 10.5}
        }
        
        mock_recommendations = {
            'quality_summary': {
                'overall': {'score': 75.0, 'rating': 'Good'},
                'clarity': {'score': 80.0, 'rating': 'Good'},
                'noise': {'score': 70.0, 'rating': 'Fair'}
            },
            'issues_detected': [
                {'issue': 'low_snr', 'severity': 'medium', 'confidence': 0.75}
            ],
            'recommendations': [
                {'action': 'add_noise_reduction', 'description': 'Apply noise reduction', 'priority': 0.8}
            ]
        }
        
        print("\nGenerating explanation...")
        explanation = explainer.explain_analysis(
            mock_dsp, {}, mock_recommendations, "test_audio.wav", "Test analysis"
        )
        
        if explanation:
            print("\n" + "=" * 60)
            print("LLM EXPLANATION:")
            print("=" * 60)
            print(explanation)
            print("=" * 60)
        else:
            print("\n⚠ Could not generate explanation")
    else:
        print(f"\n⚠ Ollama not available: {status.get('error', 'Unknown error')}")
        print("\nInstall Ollama:")
        print("  1. Visit: https://ollama.ai")
        print("  2. Download and install")
        print("  3. Run: ollama pull mistral")
        print("  4. Ollama API runs on http://localhost:11434")
