"""
BallotGuard Performance Visualization for IEEE Paper
Generates publication-quality graphs from benchmark data
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# Set publication-quality parameters
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 13

# IEEE color palette (colorblind-friendly)
IEEE_COLORS = {
    'blue': '#0072BD',
    'orange': '#D95319',
    'yellow': '#EDB120',
    'purple': '#7E2F8E',
    'green': '#77AC30',
    'cyan': '#4DBEEE',
    'red': '#A2142F'
}

def load_benchmark_data():
    """Load benchmark results from JSON files"""
    with open('benchmark_results.json', 'r') as f:
        crypto_data = json.load(f)
    
    with open('benchmark_e2e_results.json', 'r') as f:
        e2e_data = json.load(f)
    
    tally_scaling_data = None
    try:
        with open('benchmark_tally_scaling_results.json', 'r') as f:
            tally_scaling_data = json.load(f)
    except FileNotFoundError:
        print("⚠️  benchmark_tally_scaling_results.json not found; Fig2 will be skipped")
    
    return crypto_data, e2e_data, tally_scaling_data


def fig1_cryptographic_operations_performance(crypto_data):
    """
    Figure 1: Individual Cryptographic Operation Timings
    Bar chart showing mean latency with error bars
    """
    operations = {
        'Paillier\nEncryption': ('paillier_encryption', IEEE_COLORS['blue']),
        'RSA-PSS\nSigning': ('rsa_pss_signing_3072', IEEE_COLORS['orange']),
        'RSA-PSS\nVerification': ('rsa_pss_verification_3072', IEEE_COLORS['green']),
        'SHA-256\nHashing': ('sha256_hashing', IEEE_COLORS['yellow']),
        'Blockchain\nVerification': ('blockchain_verification', IEEE_COLORS['purple']),
        'Face Distance\nCalculation': ('face_distance_calculation', IEEE_COLORS['cyan'])
    }
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    labels = []
    means = []
    stds = []
    colors = []
    
    for label, (key, color) in operations.items():
        if key in crypto_data:
            labels.append(label)
            means.append(crypto_data[key]['mean'])
            stds.append(crypto_data[key]['std'])
            colors.append(color)
    
    x_pos = np.arange(len(labels))
    bars = ax.bar(x_pos, means, yerr=stds, capsize=5, color=colors, 
                   alpha=0.85, edgecolor='black', linewidth=0.8, 
                   error_kw={'elinewidth': 1.5, 'capthick': 1.5})
    
    ax.set_xlabel('Cryptographic Operation', fontweight='bold')
    ax.set_ylabel('Mean Latency (milliseconds)', fontweight='bold')
    ax.set_title('Figure 1: Individual Cryptographic Operation Performance\n' + 
                 'Intel Core i7-10700K @ 3.80GHz, 16GB RAM, Windows 11',
                 fontweight='bold', pad=15)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, rotation=0, ha='center')
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Add value labels on bars
    for i, (bar, mean, std) in enumerate(zip(bars, means, stds)):
        height = bar.get_height()
        if mean < 1:
            label_text = f'{mean:.3f}±{std:.3f}'
        else:
            label_text = f'{mean:.1f}±{std:.1f}'
        ax.text(bar.get_x() + bar.get_width()/2., height + std + max(means)*0.02,
                label_text, ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.savefig('fig1_crypto_operations.png', bbox_inches='tight')
    plt.savefig('fig1_crypto_operations.pdf', bbox_inches='tight')
    print("✓ Generated: fig1_crypto_operations.png/pdf")
    plt.close()


def fig2_homomorphic_tallying_scalability(tally_scaling_data):
    """
    Figure 2: Homomorphic Tallying Performance vs Vote Count
    Line chart with markers showing O(n) complexity
    """
    if not tally_scaling_data or 'scale_test' not in tally_scaling_data:
        print("⚠️  Skipping Fig2: tally_scaling_data not available")
        return
    
    tally_data = tally_scaling_data['scale_test']
    
    vote_counts = [entry['voter_count'] for entry in tally_data]
    times = [entry['homomorphic_ms'] for entry in tally_data]
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Plot actual data
    ax.plot(vote_counts, times, marker='o', markersize=8, linewidth=2.5,
            color=IEEE_COLORS['blue'], label='Measured Performance',
            markerfacecolor='white', markeredgewidth=2)
    
    # Add theoretical O(n) reference line
    theoretical = np.array(vote_counts) * (times[0] / vote_counts[0])
    ax.plot(vote_counts, theoretical, linestyle='--', linewidth=2,
            color=IEEE_COLORS['red'], alpha=0.7, label='Theoretical O(n)')
    
    ax.set_xlabel('Number of Encrypted Votes', fontweight='bold')
    ax.set_ylabel('Tallying Time (milliseconds)', fontweight='bold')
    ax.set_title('Figure 2: Homomorphic Tallying Scalability\n' +
                 'Paillier-3072 Homomorphic Addition Performance',
                 fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc='upper left', framealpha=0.95)
    
    # Add data point labels
    for x, y in zip(vote_counts, times):
        ax.annotate(f'{y:.1f}ms', (x, y), textcoords="offset points",
                   xytext=(0, 10), ha='center', fontsize=8,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                            edgecolor='gray', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('fig2_tallying_scalability.png', bbox_inches='tight')
    plt.savefig('fig2_tallying_scalability.pdf', bbox_inches='tight')
    print("✓ Generated: fig2_tallying_scalability.png/pdf")
    plt.close()


def fig3_end_to_end_latency_breakdown(e2e_data):
    """
    Figure 3: End-to-End Vote Submission Latency Breakdown
    Stacked bar chart showing component contributions
    """
    components = e2e_data['components']
    
    # Extract data
    labels = ['Face\nAuthentication', 'OVT\nIssuance', 'Vote\nCasting']
    times = [
        components['face_auth']['mean'],
        components['ovt_issue']['mean'],
        components['vote_cast']['mean']
    ]
    colors = [IEEE_COLORS['green'], IEEE_COLORS['orange'], IEEE_COLORS['blue']]
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Create stacked bar
    bottom = 0
    bars = []
    for i, (label, time, color) in enumerate(zip(labels, times, colors)):
        bar = ax.bar(0, time, bottom=bottom, color=color, edgecolor='black',
                    linewidth=1.2, alpha=0.85, width=0.4)
        bars.append(bar)
        
        # Add percentage label
        total = sum(times)
        percentage = (time / total) * 100
        y_pos = bottom + time / 2
        ax.text(0, y_pos, f'{label}\n{time:.1f}ms\n({percentage:.1f}%)',
               ha='center', va='center', fontweight='bold', fontsize=10,
               color='white' if i != 0 else 'black')
        bottom += time
    
    ax.set_ylabel('Cumulative Latency (milliseconds)', fontweight='bold')
    ax.set_title('Figure 3: End-to-End Vote Submission Latency Breakdown\n' +
                 f'Total: {sum(times):.1f}ms (~{sum(times)/1000:.1f} seconds)',
                 fontweight='bold', pad=15)
    ax.set_xlim(-0.3, 0.3)
    ax.set_xticks([])
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Add total line
    ax.axhline(y=sum(times), color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax.text(0.05, sum(times), f'  Total: {sum(times):.1f}ms', 
           va='center', fontweight='bold', color='red')
    
    plt.tight_layout()
    plt.savefig('fig3_e2e_latency.png', bbox_inches='tight')
    plt.savefig('fig3_e2e_latency.pdf', bbox_inches='tight')
    print("✓ Generated: fig3_e2e_latency.png/pdf")
    plt.close()


def fig4_latency_comparison_grouped(crypto_data, e2e_data):
    """
    Figure 4: Latency Comparison Across System Components
    Grouped bar chart comparing different operation categories
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    
    categories = ['Cryptographic\nOperations', 'End-to-End\nWorkflow']
    
    # Cryptographic operations (averages)
    crypto_ops = [
        crypto_data['paillier_encryption']['mean'],
        crypto_data['rsa_pss_signing_3072']['mean'],
        crypto_data['rsa_pss_verification_3072']['mean']
    ]
    crypto_avg = np.mean(crypto_ops)
    
    # E2E components
    e2e_components = e2e_data['components']
    e2e_avg = (e2e_components['face_auth']['mean'] + 
               e2e_components['ovt_issue']['mean'] + 
               e2e_components['vote_cast']['mean']) / 3
    
    values = [crypto_avg, e2e_avg]
    colors_list = [IEEE_COLORS['blue'], IEEE_COLORS['orange']]
    
    bars = ax.bar(categories, values, color=colors_list, alpha=0.85,
                  edgecolor='black', linewidth=1.2, width=0.5)
    
    ax.set_ylabel('Average Latency (milliseconds)', fontweight='bold')
    ax.set_title('Figure 4: System Component Latency Comparison',
                 fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Add value labels
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.02,
                f'{val:.1f}ms', ha='center', va='bottom', 
                fontweight='bold', fontsize=11)
    
    plt.tight_layout()
    plt.savefig('fig4_latency_comparison.png', bbox_inches='tight')
    plt.savefig('fig4_latency_comparison.pdf', bbox_inches='tight')
    print("✓ Generated: fig4_latency_comparison.png/pdf")
    plt.close()


def fig5_component_percentage_pie(e2e_data):
    """
    Figure 5: Vote Submission Time Distribution (Pie Chart)
    Shows percentage contribution of each component
    """
    components = e2e_data['components']
    
    labels = ['Face Authentication', 'OVT Issuance', 'Vote Casting']
    sizes = [
        components['face_auth']['mean'],
        components['ovt_issue']['mean'],
        components['vote_cast']['mean']
    ]
    colors = [IEEE_COLORS['green'], IEEE_COLORS['orange'], IEEE_COLORS['blue']]
    explode = (0.05, 0.05, 0.05)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels,
                                       colors=colors, autopct='%1.1f%%',
                                       shadow=True, startangle=90,
                                       textprops={'fontsize': 11, 'weight': 'bold'},
                                       wedgeprops={'edgecolor': 'black', 'linewidth': 1.5})
    
    # Make percentage text white and bold
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(12)
        autotext.set_weight('bold')
    
    ax.set_title('Figure 5: End-to-End Latency Distribution\n' +
                 f'Total Time: {sum(sizes):.1f}ms',
                 fontweight='bold', pad=20, fontsize=13)
    
    # Add legend with actual times
    legend_labels = [f'{label}: {size:.1f}ms' for label, size in zip(labels, sizes)]
    ax.legend(legend_labels, loc='upper left', bbox_to_anchor=(0.85, 1),
             framealpha=0.95, fontsize=10)
    
    plt.tight_layout()
    plt.savefig('fig5_time_distribution.png', bbox_inches='tight')
    plt.savefig('fig5_time_distribution.pdf', bbox_inches='tight')
    print("✓ Generated: fig5_time_distribution.png/pdf")
    plt.close()


def fig6_security_overhead_analysis(crypto_data):
    """
    Figure 6: Security vs Performance Trade-off
    Bar chart comparing operations with security annotations
    """
    operations = [
        ('Paillier\nEncryption', crypto_data['paillier_encryption']['mean'], 
         '3072-bit\nIND-CPA', IEEE_COLORS['blue']),
        ('RSA-PSS\nSigning', crypto_data['rsa_pss_signing_3072']['mean'],
         '3072-bit\nEUF-CMA', IEEE_COLORS['orange']),
        ('RSA-PSS\nVerify', crypto_data['rsa_pss_verification_3072']['mean'],
         '3072-bit\nEUF-CMA', IEEE_COLORS['green']),
        ('SHA-256\nHash', crypto_data['sha256_hashing']['mean'],
         '256-bit\nCollision', IEEE_COLORS['yellow'])
    ]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    labels = [op[0] for op in operations]
    times = [op[1] for op in operations]
    security = [op[2] for op in operations]
    colors = [op[3] for op in operations]
    
    x_pos = np.arange(len(labels))
    bars = ax.bar(x_pos, times, color=colors, alpha=0.85,
                  edgecolor='black', linewidth=1.2)
    
    ax.set_xlabel('Cryptographic Operation', fontweight='bold')
    ax.set_ylabel('Latency (milliseconds, log scale)', fontweight='bold')
    ax.set_title('Figure 6: Cryptographic Security vs Performance Trade-off',
                 fontweight='bold', pad=15)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels)
    ax.set_yscale('log')
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Add security level annotations
    for i, (bar, time, sec) in enumerate(zip(bars, times, security)):
        ax.text(bar.get_x() + bar.get_width()/2., time * 1.5,
                sec, ha='center', va='bottom', fontsize=8,
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                         edgecolor='gray', alpha=0.9))
    
    plt.tight_layout()
    plt.savefig('fig6_security_performance.png', bbox_inches='tight')
    plt.savefig('fig6_security_performance.pdf', bbox_inches='tight')
    print("✓ Generated: fig6_security_performance.png/pdf")
    plt.close()


def generate_all_figures():
    """Generate all performance visualization figures"""
    print("\n" + "="*60)
    print("BallotGuard Performance Graph Generator")
    print("Generating IEEE publication-quality figures...")
    print("="*60 + "\n")
    
    # Load data
    print("Loading benchmark data...")
    crypto_data, e2e_data, tally_scaling_data = load_benchmark_data()
    print("✓ Data loaded successfully\n")
    
    # Generate all figures
    print("Generating figures...")
    fig1_cryptographic_operations_performance(crypto_data)
    fig2_homomorphic_tallying_scalability(tally_scaling_data)
    fig3_end_to_end_latency_breakdown(e2e_data)
    fig4_latency_comparison_grouped(crypto_data, e2e_data)
    fig5_component_percentage_pie(e2e_data)
    fig6_security_overhead_analysis(crypto_data)
    
    print("\n" + "="*60)
    print("✓ All figures generated successfully!")
    print("="*60)
    print("\nGenerated files:")
    print("  - fig1_crypto_operations.png/pdf")
    print("  - fig2_tallying_scalability.png/pdf")
    print("  - fig3_e2e_latency.png/pdf")
    print("  - fig4_latency_comparison.png/pdf")
    print("  - fig5_time_distribution.png/pdf")
    print("  - fig6_security_performance.png/pdf")
    print("\nUse PNG for Word documents, PDF for LaTeX/IEEE submission")
    print("="*60 + "\n")


if __name__ == "__main__":
    generate_all_figures()
