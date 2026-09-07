-- Confirmed Chinese OCR typo. Preserve later edits and vocabulary IDs.
UPDATE vocabulary_items
SET meaning_zh = '西班牙的', updated_at = CURRENT_TIMESTAMP
WHERE word = 'испанский' AND meaning_zh = '西珠牙的';
