"""
app/panels/events.py — Panel 3: Events to Attend.

render_events(event_recs, calendar_push_ready) renders event cards
and an optional "Add All to Google Calendar" button.
"""

import streamlit as st

from schemas.agent2 import EventRecommendation


def render_events(
    event_recs: list[EventRecommendation],
    calendar_push_ready: bool,
) -> None:
    """Render the Events to Attend panel into the current Streamlit column."""
    st.markdown("## 🗓️ Events to Attend")

    for event in event_recs:
        dt_str = event.event_datetime.strftime("%a, %b %d · %I:%M %p UTC")
        st.markdown(
            f"""
<div class="uniflow-card">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div style="font-size:1rem;font-weight:600;color:#e2e8f0;">{event.title}</div>
        <span class="badge badge-event">{event.event_type.replace("_", " ")}</span>
    </div>
    <div style="color:#94a3b8;font-size:0.82rem;margin-top:0.4rem;">🏢 {event.organiser}</div>
    <div style="color:#94a3b8;font-size:0.82rem;">📅 {dt_str}</div>
    <div style="color:#94a3b8;font-size:0.82rem;">📍 {event.location}</div>
    <div style="color:#c7d2fe;font-size:0.84rem;margin-top:0.4rem;">💡 {event.relevance_reason}</div>
    <div style="margin-top:0.75rem;">
        <a href="{event.url}" target="_blank"
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
