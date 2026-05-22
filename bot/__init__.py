"""Telegram bot wrapper -- back-squat hypertrophy coach.

Receives Telegram messages + videos, runs pose extraction (pose/), builds a
system prompt from coach/ folder + per-user profile.md (DC-21), calls Claude,
replies. DC-22 read-before-write enforced on all profile.md mutations.
"""
