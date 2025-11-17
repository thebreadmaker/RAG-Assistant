#!/usr/bin/env python3
"""
Log Analyzer - Debug tool for analyzing RAG Assistant logs
Usage: python analyze_logs.py <log_file> [--errors-only] [--query <search_term>]
"""

import sys
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import argparse

def analyze_logs(log_file: str, errors_only: bool = False, query_term: str = None):
    """Analyze logs for patterns, errors, and debugging information."""
    
    path = Path(log_file)
    
    if not path.exists():
        print(f"❌ Log file not found: {log_file}")
        return
    
    print(f"\n{'='*80}")
    print(f"📊 Log Analysis Report")
    print(f"{'='*80}")
    print(f"File: {log_file}")
    print(f"Size: {path.stat().st_size / 1024:.2f} KB")
    print(f"{'='*80}\n")
    
    errors = []
    warnings = []
    info_logs = []
    debug_logs = []
    error_counts = defaultdict(int)
    check_patterns = defaultdict(int)
    response_times = []
    cache_stats = {"hits": 0, "misses": 0}
    retrieval_stats = {"total": 0, "semantic": 0, "bm25": 0}
    llm_calls = []
    eligibility_checks = []
    
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Filter by query term if provided
            if query_term and query_term.lower() not in line.lower():
                continue
            
            # Categorize by level
            if 'ERROR' in line or '❌' in line:
                errors.append(line)
                # Extract error type
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        error_type = parts[0][-40:]  # Last 40 chars
                        error_counts[error_type] += 1
                        
            elif 'WARNING' in line or '⚠️' in line:
                warnings.append(line)
            elif 'DEBUG' in line:
                debug_logs.append(line)
            elif 'INFO' in line or any(x in line for x in ['📥', '📤', '🔍', '🤖', '👤', '✅', '🏥', '💾']):
                info_logs.append(line)
            
            # Parse response times (duration in seconds)
            if 'Duration:' in line or 'duration:' in line.lower():
                try:
                    parts = line.split('duration:')[-1].split()[0]
                    duration = float(parts.rstrip('s'))
                    response_times.append(duration)
                except:
                    pass
            
            # Track cache hits/misses
            if 'Cache HIT' in line or 'cache hit' in line.lower():
                cache_stats["hits"] += 1
            elif 'Cache MISS' in line or 'cache miss' in line.lower():
                cache_stats["misses"] += 1
            
            # Track retrieval statistics
            if 'Semantic search:' in line or 'Retrieved' in line:
                retrieval_stats["total"] += 1
            if 'Semantic search:' in line:
                retrieval_stats["semantic"] += 1
            if 'BM25' in line:
                retrieval_stats["bm25"] += 1
            
            # Track LLM calls
            if 'LLM call:' in line or '🤖' in line:
                llm_calls.append(line)
            
            # Track eligibility checks
            if 'check started' in line.lower() or '👤' in line:
                eligibility_checks.append(line)
            
            # Track check results
            for keyword in ['DPD_Arrears_Check_DS', 'customer_vintage_Check', 'Turnover_Check', 'Active_Inactive_Check']:
                if keyword in line:
                    check_patterns[keyword] += 1
    
    # Print summary statistics
    print(f"📊 SUMMARY STATISTICS")
    print(f"{'-'*80}")
    print(f"Total Info Logs:        {len(info_logs)}")
    print(f"Total Debug Logs:       {len(debug_logs)}")
    print(f"Total Warnings:         {len(warnings)}")
    print(f"Total Errors:           {len(errors)}")
    print()
    
    # Performance metrics
    if response_times:
        print(f"⏱️  RESPONSE TIME METRICS")
        print(f"{'-'*80}")
        print(f"Total requests:        {len(response_times)}")
        print(f"Min time:              {min(response_times):.3f}s")
        print(f"Max time:              {max(response_times):.3f}s")
        print(f"Avg time:              {sum(response_times)/len(response_times):.3f}s")
        print(f"Median time:           {sorted(response_times)[len(response_times)//2]:.3f}s")
        print()
    
    # Cache statistics
    if cache_stats["hits"] + cache_stats["misses"] > 0:
        total = cache_stats["hits"] + cache_stats["misses"]
        hit_rate = (cache_stats["hits"] / total * 100) if total > 0 else 0
        print(f"💾 CACHE STATISTICS")
        print(f"{'-'*80}")
        print(f"Cache Hits:            {cache_stats['hits']}")
        print(f"Cache Misses:          {cache_stats['misses']}")
        print(f"Hit Rate:              {hit_rate:.1f}%")
        print()
    
    # Retrieval statistics
    if retrieval_stats["total"] > 0:
        print(f"🔍 RETRIEVAL STATISTICS")
        print(f"{'-'*80}")
        print(f"Total retrievals:      {retrieval_stats['total']}")
        print(f"Semantic searches:     {retrieval_stats['semantic']}")
        print(f"BM25 fallbacks:        {retrieval_stats['bm25']}")
        print()
    
    # Check patterns
    if check_patterns:
        print(f"📋 ELIGIBILITY CHECK PATTERNS")
        print(f"{'-'*80}")
        for check_type, count in sorted(check_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"{check_type:.<40} {count:>5}")
        print()
    
    # Error summary
    if errors:
        print(f"🔴 ERROR SUMMARY (Top 10)")
        print(f"{'-'*80}")
        error_summary = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for error_type, count in error_summary:
            print(f"{error_type:.<70} {count:>5}")
        print()
        
        if not errors_only:
            print(f"First 3 errors:")
            for i, error in enumerate(errors[:3], 1):
                print(f"{i}. {error[:150]}..." if len(error) > 150 else f"{i}. {error}")
            print()
    
    # Warnings summary
    if warnings and not errors_only:
        print(f"⚠️  WARNINGS (Last 5)")
        print(f"{'-'*80}")
        for warning in warnings[-5:]:
            print(f"   {warning[:150]}..." if len(warning) > 150 else f"   {warning}")
        print()
    
    # Debug search
    if query_term:
        print(f"🔎 SEARCH RESULTS FOR: '{query_term}'")
        print(f"{'-'*80}")
        all_matching = [l for l in info_logs + debug_logs + warnings + errors if query_term.lower() in l.lower()]
        for line in all_matching[:10]:
            print(f"   {line}")
        if len(all_matching) > 10:
            print(f"   ... and {len(all_matching) - 10} more results")
        print()
    
    # Recent activity
    if not errors_only:
        print(f"📜 RECENT ACTIVITY (Last 10 INFO logs)")
        print(f"{'-'*80}")
        for log in info_logs[-10:]:
            print(f"   {log}")
        print()
    
    print(f"{'='*80}")
    print(f"✅ Analysis complete\n")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze RAG Assistant logs for debugging and monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_logs.py ../logs/all_*.log
  python analyze_logs.py ../logs/errors_*.log --errors-only
  python analyze_logs.py ../logs/all_*.log --query "customer_id"
  python analyze_logs.py ../logs/all_*.log --query "ERROR"
        """
    )
    
    parser.add_argument('logfile', help='Path to log file (supports wildcards)')
    parser.add_argument('--errors-only', action='store_true', help='Show only errors')
    parser.add_argument('--query', type=str, help='Search for specific term in logs')
    
    args = parser.parse_args()
    
    # Handle wildcard patterns
    log_file = args.logfile
    
    # If wildcard pattern, use the most recent matching file
    if '*' in log_file:
        from glob import glob
        matches = sorted(glob(log_file), reverse=True)
        if not matches:
            print(f"❌ No log files matching pattern: {log_file}")
            sys.exit(1)
        log_file = matches[0]
        print(f"Using latest log file: {log_file}\n")
    
    analyze_logs(log_file, args.errors_only, args.query)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
Usage: python analyze_logs.py <log_file> [options]

Options:
  --errors-only        Show only errors
  --query <term>       Search for specific term

Examples:
  python analyze_logs.py ../logs/all_*.log
  python analyze_logs.py ../logs/errors_*.log --errors-only
  python analyze_logs.py ../logs/all_*.log --query "customer_id"
        """)
        sys.exit(1)
    
    main()
