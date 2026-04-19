"""
Visualisointifunktiot analyysituloksille
"""

import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, Optional


def create_analysis_visualizations(y: np.ndarray,
                                   sr: int,
                                   dsp_results: Dict,
                                   recommendations: Dict,
                                   output_path: str):
    """
    Luo kattavat visualisoinnit analyysituloksista
    
    Args:
        y: Audio signal
        sr: Sample rate
        dsp_results: DSP analysis results
        recommendations: Recommendations dict
        output_path: Path to save figure
    """
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    
    # Convert to mono if stereo
    if y.ndim > 1:
        y_mono = librosa.to_mono(y)
        is_stereo = True
    else:
        y_mono = y
        is_stereo = False
    
    # 1. Waveform (top)
    ax1 = plt.subplot(4, 2, 1)
    librosa.display.waveshow(y_mono, sr=sr, alpha=0.6, ax=ax1)
    ax1.set_title('Aaltomuoto', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Aika (s)')
    ax1.set_ylabel('Amplitudi')
    
    # 2. Spectrogram
    ax2 = plt.subplot(4, 2, 2)
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y_mono)), ref=np.max)
    img2 = librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='hz', ax=ax2, cmap='viridis')
    ax2.set_ylim(0, 10000)
    ax2.set_title('Spektrogrammi', fontsize=12, fontweight='bold')
    plt.colorbar(img2, ax=ax2, format='%+2.0f dB')
    
    # 3. Mel Spectrogram
    ax3 = plt.subplot(4, 2, 3)
    mel_spec = librosa.feature.melspectrogram(y=y_mono, sr=sr, n_mels=128)
    mel_spec_db = librosa.amplitude_to_db(mel_spec, ref=np.max)
    img3 = librosa.display.specshow(mel_spec_db, sr=sr, x_axis='time', y_axis='mel', ax=ax3, cmap='magma')
    ax3.set_title('Mel-Spektrogrammi', fontsize=12, fontweight='bold')
    plt.colorbar(img3, ax=ax3, format='%+2.0f dB')
    
    # 4. Frequency Balance
    ax4 = plt.subplot(4, 2, 4)
    if 'frequency_balance' in dsp_results:
        band_energies = dsp_results['frequency_balance'].get('band_energies_db', {})
        if band_energies:
            bands = list(band_energies.keys())
            energies = list(band_energies.values())
            
            bars = ax4.bar(range(len(bands)), energies, color='skyblue', edgecolor='navy', alpha=0.7)
            ax4.set_xticks(range(len(bands)))
            ax4.set_xticklabels(bands, rotation=45, ha='right')
            ax4.set_ylabel('Energia (dB)')
            ax4.set_title('Taajuustasapaino', fontsize=12, fontweight='bold')
            ax4.grid(axis='y', alpha=0.3)
            
            # Highlight dominant range
            dominant = dsp_results['frequency_balance'].get('dominant_range', '')
            if dominant and dominant in bands:
                idx = bands.index(dominant)
                bars[idx].set_color('orange')
    
    # 5. Dynamic Range visualization
    ax5 = plt.subplot(4, 2, 5)
    rms = librosa.feature.rms(y=y_mono)[0]
    times = librosa.times_like(rms, sr=sr)
    rms_db = 20 * np.log10(rms + 1e-10)
    
    ax5.plot(times, rms_db, color='green', linewidth=1, alpha=0.7)
    ax5.fill_between(times, rms_db, np.min(rms_db), color='green', alpha=0.3)
    
    if 'dynamic_range' in dsp_results:
        dr = dsp_results['dynamic_range']
        peak_db = dr.get('peak_db', 0)
        ax5.axhline(y=peak_db, color='red', linestyle='--', label=f'Peak: {peak_db:.1f} dB')
        ax5.legend()
    
    ax5.set_xlabel('Aika (s)')
    ax5.set_ylabel('RMS (dB)')
    ax5.set_title('Dynaaminen vaihtelu', fontsize=12, fontweight='bold')
    ax5.grid(alpha=0.3)
    
    # 6. Quality Scores Radar Chart
    ax6 = plt.subplot(4, 2, 6, projection='polar')
    if 'quality_summary' in recommendations:
        categories = []
        scores = []
        
        for aspect, data in recommendations['quality_summary'].items():
            if aspect != 'overall':
                categories.append(aspect.replace('_', '\n'))
                scores.append(data['score'])
        
        if categories:
            # Number of variables
            N = len(categories)
            
            # Compute angle for each axis
            angles = [n / float(N) * 2 * np.pi for n in range(N)]
            scores += scores[:1]  # Complete the circle
            angles += angles[:1]
            
            # Plot
            ax6.plot(angles, scores, 'o-', linewidth=2, color='blue', label='Pisteet')
            ax6.fill(angles, scores, alpha=0.25, color='blue')
            
            # Fix axis to go from 0 to 100
            ax6.set_ylim(0, 100)
            ax6.set_xticks(angles[:-1])
            ax6.set_xticklabels(categories, size=8)
            ax6.set_title('Laatupisteet', fontsize=12, fontweight='bold', pad=20)
            ax6.grid(True)
            
            # Add reference circle at 50
            ax6.plot(angles, [50]*len(angles), '--', color='gray', alpha=0.5, linewidth=1)
    
    # 7. Stereo Field (if stereo)
    ax7 = plt.subplot(4, 2, 7)
    if is_stereo and 'stereo' in dsp_results:
        left = y[0]
        right = y[1]
        
        # Sample for scatter plot (use downsampled data)
        downsample_factor = max(1, len(left) // 10000)
        left_sampled = left[::downsample_factor]
        right_sampled = right[::downsample_factor]
        
        ax7.scatter(left_sampled, right_sampled, alpha=0.1, s=1, color='purple')
        ax7.plot([-1, 1], [-1, 1], 'r--', alpha=0.5, label='Mono line')
        ax7.set_xlabel('Left Channel')
        ax7.set_ylabel('Right Channel')
        ax7.set_title('Stereo Field', fontsize=12, fontweight='bold')
        ax7.set_xlim(-1, 1)
        ax7.set_ylim(-1, 1)
        ax7.grid(alpha=0.3)
        ax7.legend()
        
        # Add correlation text
        corr = dsp_results['stereo'].get('phase_correlation', 0)
        ax7.text(0.05, 0.95, f'Correlation: {corr:.2f}',
                transform=ax7.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    else:
        ax7.text(0.5, 0.5, 'Mono Audio\n(No stereo analysis)',
                ha='center', va='center', fontsize=14, color='gray')
        ax7.set_title('Stereo Field', fontsize=12, fontweight='bold')
        ax7.axis('off')
    
    # 8. Issues and Recommendations
    ax8 = plt.subplot(4, 2, 8)
    ax8.axis('off')
    
    # Title
    ax8.text(0.5, 0.95, 'Yhteenveto', fontsize=14, fontweight='bold',
            ha='center', transform=ax8.transAxes)
    
    # Overall score
    if 'quality_summary' in recommendations and 'overall' in recommendations['quality_summary']:
        overall_score = recommendations['quality_summary']['overall']['score']
        overall_rating = recommendations['quality_summary']['overall']['rating']
        
        ax8.text(0.5, 0.85, f'Kokonaisarvosana: {overall_score:.0f}/100',
                fontsize=12, ha='center', transform=ax8.transAxes,
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
        ax8.text(0.5, 0.77, f'({overall_rating})',
                fontsize=10, ha='center', transform=ax8.transAxes)
    
    # Issues
    y_pos = 0.65
    if recommendations.get('issues_detected'):
        ax8.text(0.05, y_pos, 'Havaitut ongelmat:', fontsize=10, fontweight='bold',
                transform=ax8.transAxes)
        y_pos -= 0.05
        
        for issue in recommendations['issues_detected'][:5]:  # Top 5
            issue_text = f"• {issue['issue'].replace('_', ' ').title()}"
            ax8.text(0.05, y_pos, issue_text, fontsize=8,
                    transform=ax8.transAxes, color='red')
            y_pos -= 0.04
    
    y_pos -= 0.05
    
    # Recommendations
    if recommendations.get('priority_actions'):
        ax8.text(0.05, y_pos, 'Tärkeimmät toimenpiteet:', fontsize=10, fontweight='bold',
                transform=ax8.transAxes)
        y_pos -= 0.05
        
        for i, action in enumerate(recommendations['priority_actions'][:5], 1):  # Top 5
            action_text = f"{i}. {action.replace('_', ' ').title()}"
            ax8.text(0.05, y_pos, action_text, fontsize=8,
                    transform=ax8.transAxes, color='blue')
            y_pos -= 0.04
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def create_comparison_chart(results_list: list, output_path: str):
    """
    Luo vertailukaavio useille tiedostoille
    
    Args:
        results_list: List of analysis results
        output_path: Path to save figure
    """
    if not results_list:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    filenames = [r['filename'] for r in results_list]
    
    # 1. Overall scores comparison
    ax1 = axes[0, 0]
    overall_scores = [r['recommendations']['quality_summary'].get('overall', {}).get('score', 0) 
                     for r in results_list]
    bars = ax1.barh(filenames, overall_scores, color='skyblue', edgecolor='navy')
    ax1.set_xlabel('Kokonaispistemäärä')
    ax1.set_title('Kokonaislaatu vertailu', fontweight='bold')
    ax1.set_xlim(0, 100)
    
    # Color code bars
    for bar, score in zip(bars, overall_scores):
        if score >= 75:
            bar.set_color('green')
        elif score >= 50:
            bar.set_color('orange')
        else:
            bar.set_color('red')
    
    # 2. SNR comparison
    ax2 = axes[0, 1]
    snrs = [r['dsp_analysis'].get('noise', {}).get('snr_db', 0) for r in results_list]
    ax2.barh(filenames, snrs, color='lightgreen', edgecolor='darkgreen')
    ax2.set_xlabel('SNR (dB)')
    ax2.set_title('Signal-to-Noise Ratio', fontweight='bold')
    ax2.axvline(x=25, color='red', linestyle='--', label='Minimum (25 dB)')
    ax2.legend()
    
    # 3. Dynamic Range comparison
    ax3 = axes[1, 0]
    drs = [r['dsp_analysis'].get('dynamic_range', {}).get('dynamic_range_db', 0) 
          for r in results_list]
    ax3.barh(filenames, drs, color='coral', edgecolor='darkred')
    ax3.set_xlabel('Dynamic Range (dB)')
    ax3.set_title('Dynaaminen alue', fontweight='bold')
    ax3.axvline(x=12, color='green', linestyle='--', label='Target (12 dB)')
    ax3.legend()
    
    # 4. Issues count comparison
    ax4 = axes[1, 1]
    issue_counts = [len(r['recommendations'].get('issues_detected', [])) 
                   for r in results_list]
    ax4.barh(filenames, issue_counts, color='salmon', edgecolor='darkred')
    ax4.set_xlabel('Ongelmien määrä')
    ax4.set_title('Havaitut ongelmat', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
