import secrets
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from app.models.survey import (
    Survey, SurveySection, SurveyQuestion, SurveyDiagnosticRule,
    SurveyCampaign, SurveyResponse, SurveyAnswer,
    SurveyQuestionType, CampaignStatus,
)
from app.schemas.survey import SurveyCreate, CampaignCreate, PublicResponseSubmit


class SurveyService:

    # ── Survey definition ────────────────────────────────────────────

    @staticmethod
    def clone_template(
        db: Session,
        template_id: int,
        organization_id: Optional[int],
        created_by: Optional[int],
    ) -> Optional[Survey]:
        """Deep-copy a template Survey (sections, questions, diagnostic_rules)
        into a new org-owned Survey with is_template=False."""
        template = db.query(Survey).filter(Survey.id == template_id).first()
        if not template:
            return None

        new_survey = Survey(
            organization_id=organization_id,
            title=template.title,
            description=template.description,
            is_template=False,
            created_by=created_by,
        )
        db.add(new_survey)
        db.flush()  # obtain new_survey.id

        for section in template.sections:
            new_section = SurveySection(
                survey_id=new_survey.id,
                title=section.title,
                order=section.order,
            )
            db.add(new_section)
            db.flush()
            for q in section.questions:
                new_q = SurveyQuestion(
                    section_id=new_section.id,
                    order=q.order,
                    text=q.text,
                    question_type=q.question_type,
                    options=q.options,
                    is_required=q.is_required,
                    scale_min=q.scale_min,
                    scale_max=q.scale_max,
                    scale_min_label=q.scale_min_label,
                    scale_max_label=q.scale_max_label,
                    diagnostic_use=q.diagnostic_use,
                )
                db.add(new_q)

        for rule in template.diagnostic_rules:
            db.add(SurveyDiagnosticRule(
                survey_id=new_survey.id,
                pattern=rule.pattern,
                suggestion=rule.suggestion,
                condition=rule.condition,
            ))

        db.commit()
        db.refresh(new_survey)
        return new_survey

    @staticmethod
    def create_survey(
        db: Session,
        data: SurveyCreate,
        organization_id: Optional[int],
        created_by: Optional[int],
    ) -> Survey:
        survey = Survey(
            organization_id=organization_id,
            title=data.title,
            description=data.description,
            is_template=False,
            created_by=created_by,
        )
        db.add(survey)
        db.flush()

        for section in data.sections:
            new_section = SurveySection(
                survey_id=survey.id,
                title=section.title,
                order=section.order,
            )
            db.add(new_section)
            db.flush()
            for q in section.questions:
                db.add(SurveyQuestion(
                    section_id=new_section.id,
                    order=q.order,
                    text=q.text,
                    question_type=q.question_type,
                    options=q.options,
                    is_required=q.is_required,
                    scale_min=q.scale_min,
                    scale_max=q.scale_max,
                    scale_min_label=q.scale_min_label,
                    scale_max_label=q.scale_max_label,
                    diagnostic_use=q.diagnostic_use,
                ))

        db.commit()
        db.refresh(survey)
        return survey

    @staticmethod
    def list_surveys(db: Session, organization_id: Optional[int]) -> List[Survey]:
        query = db.query(Survey)
        if organization_id is not None:
            query = query.filter(
                (Survey.is_template == True) | (Survey.organization_id == organization_id)
            )
        # organization_id None → return templates + all (no extra filter)
        return query.all()

    # ── Campaigns ────────────────────────────────────────────────────

    @staticmethod
    def create_campaign(
        db: Session,
        survey_id: int,
        data: CampaignCreate,
        organization_id: Optional[int],
        created_by: Optional[int],
    ) -> SurveyCampaign:
        # generate a unique public token (retry on collision)
        token = secrets.token_urlsafe(9)
        while db.query(SurveyCampaign).filter(
            SurveyCampaign.public_token == token
        ).first() is not None:
            token = secrets.token_urlsafe(9)

        campaign = SurveyCampaign(
            survey_id=survey_id,
            organization_id=organization_id,
            workspace_id=data.workspace_id,
            name=data.name,
            public_token=token,
            status=CampaignStatus.DRAFT,
            is_anonymous=data.is_anonymous,
            collect_email=data.collect_email,
            opens_at=data.opens_at,
            closes_at=data.closes_at,
            max_responses=data.max_responses,
            created_by=created_by,
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def get_public_view(db: Session, token: str) -> Optional[SurveyCampaign]:
        return (
            db.query(SurveyCampaign)
            .options(
                joinedload(SurveyCampaign.survey)
                .joinedload(Survey.sections)
                .joinedload(SurveySection.questions)
            )
            .filter(SurveyCampaign.public_token == token)
            .first()
        )

    @staticmethod
    def _all_questions(survey: Survey) -> List[SurveyQuestion]:
        questions: List[SurveyQuestion] = []
        for section in sorted(survey.sections, key=lambda s: s.order or 0):
            for q in sorted(section.questions, key=lambda x: x.order or 0):
                questions.append(q)
        return questions

    @staticmethod
    def submit_response(
        db: Session,
        campaign: SurveyCampaign,
        data: PublicResponseSubmit,
        meta: dict,
    ) -> SurveyResponse:
        survey = campaign.survey
        questions = {q.id: q for q in SurveyService._all_questions(survey)}

        # index submitted answers by question_id
        submitted = {a.question_id: a for a in data.answers}

        def _is_empty(answer, qtype: SurveyQuestionType) -> bool:
            if answer is None:
                return True
            if qtype == SurveyQuestionType.OPEN_TEXT:
                return answer.value_text is None or str(answer.value_text).strip() == ""
            if qtype == SurveyQuestionType.LINEAR_SCALE:
                return answer.value_number is None
            # SINGLE_CHOICE / MULTI_CHOICE
            return not answer.value_options

        # validate required questions
        for q in questions.values():
            if q.is_required and _is_empty(submitted.get(q.id), q.question_type):
                raise ValueError(f"La pregunta obligatoria '{q.text}' no fue respondida.")

        response = SurveyResponse(
            campaign_id=campaign.id,
            respondent_email=data.respondent_email,
            respondent_name=data.respondent_name,
            meta=meta,
            visibility="CLIENT_UPLOAD",
        )
        db.add(response)
        db.flush()

        for answer in data.answers:
            q = questions.get(answer.question_id)
            if q is None:
                continue  # ignore answers for unknown questions
            row = SurveyAnswer(response_id=response.id, question_id=q.id)
            if q.question_type == SurveyQuestionType.OPEN_TEXT:
                row.value_text = answer.value_text
            elif q.question_type == SurveyQuestionType.LINEAR_SCALE:
                row.value_number = answer.value_number
            else:  # SINGLE_CHOICE / MULTI_CHOICE
                row.value_options = answer.value_options
            db.add(row)

        db.commit()
        db.refresh(response)
        return response

    # ── Aggregation ──────────────────────────────────────────────────

    @staticmethod
    def aggregate_results(db: Session, campaign_id: int) -> Optional[dict]:
        campaign = (
            db.query(SurveyCampaign)
            .options(
                joinedload(SurveyCampaign.survey)
                .joinedload(Survey.sections)
                .joinedload(SurveySection.questions),
                joinedload(SurveyCampaign.responses)
                .joinedload(SurveyResponse.answers),
            )
            .filter(SurveyCampaign.id == campaign_id)
            .first()
        )
        if not campaign:
            return None

        survey = campaign.survey
        responses = campaign.responses
        response_count = len(responses)

        # gather answers grouped by question_id
        answers_by_question: dict = {}
        for resp in responses:
            for ans in resp.answers:
                answers_by_question.setdefault(ans.question_id, []).append(ans)

        questions_out: List[dict] = []
        for section in sorted(survey.sections, key=lambda s: s.order or 0):
            for q in sorted(section.questions, key=lambda x: x.order or 0):
                q_answers = answers_by_question.get(q.id, [])
                entry = {
                    "question_id": q.id,
                    "order": q.order,
                    "section_title": section.title,
                    "text": q.text,
                    "question_type": q.question_type.value,
                }

                if q.question_type in (SurveyQuestionType.SINGLE_CHOICE, SurveyQuestionType.MULTI_CHOICE):
                    option_counts = {opt: 0 for opt in (q.options or [])}
                    for ans in q_answers:
                        for opt in (ans.value_options or []):
                            option_counts[opt] = option_counts.get(opt, 0) + 1
                    entry["option_counts"] = option_counts

                elif q.question_type == SurveyQuestionType.LINEAR_SCALE:
                    numbers = [ans.value_number for ans in q_answers if ans.value_number is not None]
                    lo = q.scale_min if q.scale_min is not None else 1
                    hi = q.scale_max if q.scale_max is not None else 5
                    distribution = {str(i): 0 for i in range(lo, hi + 1)}
                    for n in numbers:
                        distribution[str(n)] = distribution.get(str(n), 0) + 1
                    entry["average"] = round(sum(numbers) / len(numbers), 2) if numbers else None
                    entry["distribution"] = distribution

                elif q.question_type == SurveyQuestionType.OPEN_TEXT:
                    entry["answers"] = [
                        ans.value_text for ans in q_answers
                        if ans.value_text is not None and str(ans.value_text).strip() != ""
                    ]

                questions_out.append(entry)

        return {
            "campaign_id": campaign.id,
            "survey_title": survey.title,
            "response_count": response_count,
            "questions": questions_out,
            "diagnostic_readings": [],
        }


class SurveyDiagnosticService:

    @staticmethod
    def evaluate(
        db: Session,
        survey_id: int,
        aggregated_questions: List[dict],
        response_count: int = 0,
    ) -> List[dict]:
        rules = db.query(SurveyDiagnosticRule).filter(
            SurveyDiagnosticRule.survey_id == survey_id
        ).all()

        # index aggregated questions by order
        by_order = {q.get("order"): q for q in aggregated_questions}

        readings: List[dict] = []
        for rule in rules:
            triggered, detail = SurveyDiagnosticService._evaluate_condition(
                rule.condition, by_order, response_count
            )
            readings.append({
                "pattern": rule.pattern,
                "suggestion": rule.suggestion,
                "triggered": triggered,
                "detail": detail,
            })
        return readings

    @staticmethod
    def _evaluate_condition(condition, by_order: dict, response_count: int = 0):
        no_condition = (False, "Sin condición automática (revisión manual)")
        if not condition or not isinstance(condition, dict):
            return no_condition

        op = condition.get("op")
        q_order = condition.get("question_order")
        if op is None or q_order is None:
            return no_condition

        question = by_order.get(q_order)
        if question is None:
            return no_condition

        try:
            if op in ("scale_gte", "scale_lte"):
                avg = question.get("average")
                value = condition.get("value")
                if avg is None or value is None:
                    return no_condition
                if op == "scale_gte":
                    triggered = avg >= value
                    detail = f"Promedio {avg} {'≥' if triggered else '<'} {value}"
                else:  # scale_lte
                    triggered = avg <= value
                    detail = f"Promedio {avg} {'≤' if triggered else '>'} {value}"
                return triggered, detail

            if op == "option_share_gte":
                option_counts = question.get("option_counts")
                value = condition.get("value")
                target_options = condition.get("options") or []
                if option_counts is None or value is None:
                    return no_condition
                denom = response_count if response_count and response_count > 0 else sum(option_counts.values())
                if denom <= 0:
                    return False, "Sin respuestas registradas"
                chosen = sum(option_counts.get(opt, 0) for opt in target_options)
                # For MULTI_CHOICE a single response may pick several target options,
                # so raw share can exceed 1.0. Clamp to 100% (heuristic intensity signal
                # for class prep; exact distinct-respondent union needs raw answers).
                share = min(chosen / denom, 1.0)
                triggered = share >= value
                detail = f"{round(share * 100)}% de las selecciones (umbral {round(value * 100)}%)"
                return triggered, detail
        except (TypeError, ValueError):
            return no_condition

        return no_condition
