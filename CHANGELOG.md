# Changelog

Agent Courses uses [Semantic Versioning](https://semver.org). Below 1.0, a minor version may make breaking changes.

## 0.1.0 (beta)

The first public beta of Agent Courses: a simpler format, written as one specification page.

- A course is a folder with `COURSE.md`. Each lesson is a folder with `LESSON.md`, and its id is the folder name.
- Optional phases are `###` headings in the course's lesson list.
- Lessons can declare checks, learner calls, objectives, quizzes and an explain-back judged by a rubric.
- Projects can be the learner's own, a folder in the course, or a pinned Git repository. Lessons can add starter files.
- Runners may keep a small, portable `progress.json` that holds no learner content.
- Only structural problems make a course invalid. Teaching-quality problems are warnings.
- The `agentcourses` command validates, describes and tests courses, and runs the conformance suite.
