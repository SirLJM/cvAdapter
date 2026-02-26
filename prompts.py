SYSTEM_PROMPT = """You are an ATS optimization expert. Adapt a CV to maximize keyword match with a job description.

RULES:
1. NEVER fabricate experience, skills, or achievements. Only reword/reorder EXISTING content.
2. Mirror exact job description terminology where the candidate has matching experience.
3. Include both acronyms and full terms when relevant (e.g. "CI/CD (Continuous Integration/Continuous Deployment)").
4. Front-load the most relevant experience and skills.
5. Quantify achievements where data exists in the original.

MODIFIABLE FIELDS (provided in input):
- intro, experience[].position, experience[].details[], skills[].name, skills[].description, skills_other, projects[].intro, projects[].role

OUTPUT: Return ONLY valid JSON (no markdown fences):
{"job_title":"extracted title","changes":[{"section":"human readable section","field_path":"dot.notation.path","original_value":"original text","adapted_value":"new text","reason":"why this improves ATS matching"}]}
Only include entries where adapted_value differs from original_value."""


def build_slim_cv(cv_language_data: dict) -> dict:
    slim = {}

    if "intro" in cv_language_data:
        slim["intro"] = cv_language_data["intro"]

    if "experience" in cv_language_data:
        slim["experience"] = []
        for exp in cv_language_data["experience"]:
            slim_exp = {}
            if "position" in exp:
                slim_exp["position"] = exp["position"]
            if "details" in exp:
                slim_exp["details"] = exp["details"]
            slim["experience"].append(slim_exp)

    if "skills" in cv_language_data:
        slim["skills"] = [
            {k: v for k, v in s.items() if k in ("name", "description")}
            for s in cv_language_data["skills"]
        ]

    if "skills_other" in cv_language_data:
        slim["skills_other"] = cv_language_data["skills_other"]

    if "projects" in cv_language_data:
        slim["projects"] = []
        for proj in cv_language_data["projects"]:
            slim_proj = {}
            if "intro" in proj:
                slim_proj["intro"] = proj["intro"]
            if "role" in proj:
                slim_proj["role"] = proj["role"]
            slim["projects"].append(slim_proj)

    return slim


def build_user_prompt(cv_data: dict, language: str, job_description: str) -> str:
    import json

    cv_language_data = cv_data[language]
    slim = build_slim_cv(cv_language_data)

    return f"""Adapt this CV ({language}) to the job description.

JOB DESCRIPTION:
{job_description}

CV DATA (modifiable fields only, array indices preserved):
{json.dumps(slim, separators=(',', ':'), ensure_ascii=False)}"""
