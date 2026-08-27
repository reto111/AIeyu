-- AIeyu TEM4 review state patch, 2026-08-27
-- Apply this file to the server database after backing it up.
-- It preserves users and learning records; it only updates the identified TEM4 source questions.

BEGIN TRANSACTION;

UPDATE questions
SET stem = 'Какое событие помогло В.В. Андрееву найти дело всей жизни?',
    review_status = 'approved',
    source_usage = 'practice',
    updated_at = CURRENT_TIMESTAMP
WHERE exam_system_id = (SELECT id FROM exam_systems WHERE code = 'TEM4_RU')
  AND source_year = 2021
  AND source_question_number = '71';

UPDATE question_options
SET option_text = 'Он начал играть на скрипке в 14 лет.',
    updated_at = CURRENT_TIMESTAMP
WHERE question_id = (
        SELECT id FROM questions
        WHERE exam_system_id = (SELECT id FROM exam_systems WHERE code = 'TEM4_RU')
          AND source_year = 2021 AND source_question_number = '71'
      )
  AND option_key = 'A';

UPDATE question_options
SET option_text = 'Он научился играть на инструментах.',
    updated_at = CURRENT_TIMESTAMP
WHERE question_id = (
        SELECT id FROM questions
        WHERE exam_system_id = (SELECT id FROM exam_systems WHERE code = 'TEM4_RU')
          AND source_year = 2021 AND source_question_number = '71'
      )
  AND option_key = 'B';

UPDATE questions
SET stem = 'Какая команда стала чемпионом мира по черлидингу в 2011 году?',
    review_status = 'approved',
    source_usage = 'practice',
    updated_at = CURRENT_TIMESTAMP
WHERE exam_system_id = (SELECT id FROM exam_systems WHERE code = 'TEM4_RU')
  AND source_year = 2021
  AND source_question_number = '88';

UPDATE questions
SET review_status = 'rejected',
    source_usage = 'source_reference_only',
    updated_at = CURRENT_TIMESTAMP
WHERE exam_system_id = (SELECT id FROM exam_systems WHERE code = 'TEM4_RU')
  AND source_year = 2021
  AND source_question_number = '74';

UPDATE questions
SET review_status = 'needs_review',
    source_usage = 'source_reference_only',
    updated_at = CURRENT_TIMESTAMP
WHERE exam_system_id = (SELECT id FROM exam_systems WHERE code = 'TEM4_RU')
  AND source_year = 2024
  AND CAST(source_question_number AS INTEGER) BETWEEN 81 AND 100;

COMMIT;
