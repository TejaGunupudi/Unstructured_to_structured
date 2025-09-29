def extract_qualifications_section(text, keyword):
    lines = text.split("\n")

    extracted_sections = []
    inside_section = False
    current_section = []

    for line in lines:
        if keyword in line and "#" in line:
            if inside_section:
                extracted_sections.append("\n".join(current_section))
                current_section = []
            inside_section = True
        elif inside_section and "#" in line:
            inside_section = False
            extracted_sections.append("\n".join(current_section))
            current_section = []
        if inside_section:
            current_section.append(line)

    if inside_section:
        extracted_sections.append("\n".join(current_section))

    return "\n".join(extracted_sections)


def extract_lines_after_supervision(self, text: str, lines_to_extract: int = 3) -> str:
    lines = text.split("\n")
    supervision_line_index = None
    for i, line in enumerate(lines):
        if "supervision" in line.lower():
            supervision_line_index = i
            break

    if supervision_line_index is not None:
        start = supervision_line_index
        end = supervision_line_index + lines_to_extract
        extracted_lines = lines[start:end]
        return "\n".join(extracted_lines)
    else:
        return ""
