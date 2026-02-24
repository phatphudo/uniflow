"""
app/panels/events.py — Panel 3: Events to Attend.

All dynamic values are HTML-escaped before injection into templates.
Event URLs are also sanitised to only allow http/https schemes.
"""

import html

import streamlit as st

from schemas.agent2 import EventRecommendation


def _e(value) -> str:
    """HTML-escape a value to string."""
    return html.escape(str(value))


def _safe_url(url: str) -> str:
    """Allow only http/https URLs to prevent javascript: injection."""
    s = str(url).strip()
    if s.startswith(("http://", "https://")):
        return html.escape(s, quote=True)
    return "#"


def render_events(
    event_recs: list[EventRecommendation],
    calendar_push_ready: bool,
) -> None:
    """Render the Events to Attend panel."""

    if not event_recs:
        st.info("No events were found for your target position and location.")
        return

    for event in event_recs:
        dt_str = _e(event.event_datetime.strftime("%a, %b %d · %I:%M %p UTC"))
        event_type_display = _e(event.event_type.replace("_", " "))
        st.markdown(
            f"""
<div class="uniflow-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div style="font-size:1rem;font-weight:600;color:#e2e8f0;">{_e(event.title)}</div>
    <span class="badge badge-event">{event_type_display}</span>
  </div>
  <div style="color:#94a3b8;font-size:0.82rem;margin-top:0.4rem;">🏢 {_e(event.organiser)}</div>
  <div style="color:#94a3b8;font-size:0.82rem;">📅 {dt_str}</div>
  <div style="color:#94a3b8;font-size:0.82rem;">📍 {_e(event.location)}</div>
  <div style="color:#c7d2fe;font-size:0.84rem;margin-top:0.4rem;">💡 {_e(event.relevance_reason)}</div>
  <div style="margin-top:0.75rem;">
    <a href="{_safe_url(str(event.url))}" target="_blank" rel="noopener noreferrer"
       style="background:linear-gradient(135deg,#6366f1,#a78bfa);color:white;
              text-decoration:none;padding:6px 16px;border-radius:8px;
              font-size:0.82rem;font-weight:500;">
      Register →
    </a>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    if calendar_push_ready:
        if st.button("📅 Add All Events to Google Calendar", use_container_width=True):
            st.success(
                "✅ Events would be added to Google Calendar (wired in Phase 5)."
            )
