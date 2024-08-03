def course_id_is_valid(course_id):
    """Validates the course ID based on your specific requirements."""
    return course_id.startswith("COURSE-") and course_id[7:].isdigit()
