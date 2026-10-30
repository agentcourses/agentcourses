"""Tools for Agent Courses: validate a course, describe it, test its checks."""

from agentcourses.course import Course, Diagnostic, Lesson, describe, load

__version__ = "0.1.0"
SPEC_VERSION = "0.1"

__all__ = ["Course", "Diagnostic", "Lesson", "SPEC_VERSION", "describe", "load"]
