# Evals

Пока source-specific тесты хранятся рядом с исследованиями:

- `studies/public-sources/evals.json`
- `studies/book-corpus/evals.json`

При реализации runtime их нужно собирать в единый прогон без копирования исходных примеров из книг.

Требования к каждому активному правилу:

- PASS case;
- REVIEW/HARD_GATE case по допустимой severity;
- negative boundary / preservation case;
- профиль документа;
- трассировка `eval → rule → source locator`.

Все примеры проекта должны быть синтетическими или созданными специально для тестов.
