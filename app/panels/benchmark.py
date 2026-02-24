"""
app/panels/benchmark.py — Panel 1: Resume Benchmark.

All dynamic values are HTML-escaped before injection into templates.
"""

import html
import re

import streamlit as st

from schemas.agent2 import GapReport


def _e(value) -> str:
    """HTML-escape a value to string."""
    return html.escape(str(value))


def _md(value) -> str:
    """Convert simple markdown (• bullets, **bold**) to HTML after escaping."""
    escaped = html.escape(str(value))
    # Bold
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
    # Ensure every • starts on its own line (model may omit newlines between bullets)
    escaped = re.sub(r'•', '\n•', escaped)
    # Bullet lines → <li> items
    lines = escaped.splitlines()
    out, in_list = [], False
    for line in lines:
        s = line.strip()
        if s.startswith('•'):
            if not in_list:
                out.append('<ul style="margin:0.3rem 0 0 0;padding-left:1.1rem;">')
                in_list = True
            out.append(f'<li style="margin-bottom:0.35rem;">{s[1:].strip()}</li>')
        else:
            if in_list:
                out.append('</ul>')
                in_list = False
            if s:
                out.append(s)
    if in_list:
        out.append('</ul>')
    return ''.join(out)


def render_benchmark(gap: GapReport) -> None:
    """Render the Resume Benchmark panel."""
    score = gap.benchmark_score

    matched_badges = "".join(
        f'<span class="badge badge-matched" style="margin:2px">{_e(s)}</span>'
        for s in gap.matched_skills
    )
    missing_badges = "".join(
        f'<span class="badge badge-missing" style="margin:2px">{_e(s)}</span>'
        for s in gap.missing_skills
    )

    st.markdown(
        f"""
<div class="uniflow-card">
  <div style="display:flex;align-items:center;gap:1.5rem;">
    <div>
      <div style="font-size:0.8rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;">Readiness Score</div>
      <div class="score-big">{score}</div>
      <div style="font-size:0.85rem;color:#94a3b8;">out of 100</div>
    </div>
    <div style="flex:1;">
      <div style="background:#1e293b;border-radius:9999px;height:12px;overflow:hidden;">
        <div style="width:{score}%;height:12px;border-radius:9999px;
                    background:linear-gradient(90deg,#6366f1,#a78bfa);
                    transition:width 1s ease;"></div>
      </div>
      <div style="margin-top:0.5rem;font-size:0.8rem;color:#64748b;">
        Target: <b style="color:#a78bfa">100</b> ·
        Current: <b style="color:#6366f1">{score}</b>
      </div>
    </div>
  </div>
  <hr style="border-color:rgba(99,102,241,0.2);margin:1rem 0;">
  <div>
    <div style="font-size:0.75rem;color:#94a3b8;margin-bottom:0.5rem;">MATCHED SKILLS</div>
    {matched_badges}
  </div>
  <div style="margin-top:0.75rem;">
    <div style="font-size:0.75rem;color:#94a3b8;margin-bottom:0.5rem;">MISSING SKILLS</div>
    {missing_badges}
  </div>
  <div style="margin-top:0.75rem;padding:0.75rem;background:rgba(239,68,68,0.08);
              border-radius:10px;border-left:3px solid #f87171;">
    <div style="font-size:0.7rem;color:#f87171;text-transform:uppercase;font-weight:600;">Top Gap</div>
    <div style="color:#fca5a5;font-weight:500;margin-top:2px;">{_md(gap.top_gap)}</div>
    <div style="color:#94a3b8;font-size:0.8rem;margin-top:4px;">{_e(gap.top_gap_evidence)}</div>
  </div>
  <div style="display:flex;gap:0.75rem;margin-top:0.75rem;">
    <div style="flex:1;padding:0.75rem;background:rgba(34,197,94,0.08);
                border-radius:10px;border-left:3px solid #4ade80;">
      <div style="font-size:0.7rem;color:#4ade80;text-transform:uppercase;font-weight:600;">Strength</div>
      <div style="color:#86efac;font-size:0.85rem;margin-top:4px;">{_md(gap.strength)}</div>
    </div>
    <div style="flex:1;padding:0.75rem;background:rgba(251,146,60,0.08);
                border-radius:10px;border-left:3px solid #fb923c;">
      <div style="font-size:0.7rem;color:#fb923c;text-transform:uppercase;font-weight:600;">Weakness</div>
      <div style="color:#fdba74;font-size:0.85rem;margin-top:4px;">{_md(gap.weakness)}</div>
    </div>
  </div>
  <div style="margin-top:0.75rem;padding:0.75rem;background:rgba(99,102,241,0.08);
              border-radius:10px;border-left:3px solid #6366f1;">
    <div style="font-size:0.7rem;color:#a78bfa;text-transform:uppercase;font-weight:600;">Tips to Enhance</div>
    <div style="color:#c4b5fd;font-size:0.85rem;margin-top:6px;line-height:1.6;">
      {_md(gap.tips_for_enhance)}
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
