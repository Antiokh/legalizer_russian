# Initial rules — legal-document book corpus

`PROJECT_REFINED` означает, что проект сужает наблюдение источника, чтобы не превращать стилевую тенденцию в универсальное жёсткое правило.

## LDB-001 — Genre determines composition

Source locator: `BOOK-MARYEVA-2015-2`, p. 121, ch. 7.  
Scope: document  
Basis: `SOURCE_DIRECT`  
Level: document  
Confidence: high

Не навязывать один универсальный порядок информации всем официальным/юридическим документам. Сначала определить жанр: композиция и степень формальной жёсткости зависят от него.

Не считать любое отклонение от шаблона ошибкой: часть жанров жёстко регламентирована, обычная деловая переписка допускает больше свободы.

## LDB-002 — Information order must express the logical relation

Source locator: `BOOK-MARYEVA-2015-2`, p. 121.  
Scope: all professional documents  
Basis: `PROJECT_REFINED`  
Level: paragraph/document  
Confidence: high

Порядок должен позволять восстановить смысловую связь: причина → следствие; тезис → аргумент → вывод; основание → просьба/решение, когда такая связь действительно есть.

Не выводить универсальную обязательную схему для любого документа.

## LDB-003 — Document editing proceeds from whole to detail

Source locators: `BOOK-NOVOSELTSEVA-2018`, pp. 73–74; `BOOK-MARYEVA-2015-2`, p. 122.  
Scope: editing workflow  
Basis: `SOURCE_REPEATED`  
Level: document  
Confidence: high

Диагностическая последовательность:

1. прочитать документ как целое и определить форму/жанр;
2. проверить формальные элементы по применимому текущему источнику;
3. проверить фактическую достаточность и внутреннюю непротиворечивость: числа, даты, имена, ссылки;
4. проверить композицию и логику;
5. выполнить языковую/стилистическую редактуру;
6. перечитать результат на смысл, логику, факты и коммуникативную задачу.

## LDB-004 — Conventional cliché is not an automatic style defect

Source locator: `BOOK-NOVOSELTSEVA-2018`, p. 7.  
Scope: official-admin / legal register  
Basis: `SOURCE_DIRECT`  
Level: phrase  
Confidence: high

Формульные выражения могут быть функциональной конвенцией официально-делового текста. Не помечать фразу только потому, что она шаблонная или часто повторяется.

Не защищает пустую бюрократическую набивку: формула должна выполнять функцию документа или быть устоявшейся профессиональной коллокацией.

## LDB-005 — Legal wording prioritizes unambiguous interpretation

Source locators: `BOOK-ABRAMOVA-2017`, pp. 129–131; `BOOK-MOTYAKINA-LOPATIN-2016`, around p. 20.  
Scope: legal documents  
Basis: `SOURCE_REPEATED`  
Level: sentence/document  
Confidence: high

Юридически значимая формулировка должна позволять определить субъекта, действие, объект, условие, исключение и последствие настолько однозначно, насколько требует жанр.

Диагностики: неоднозначный референт; неясный scope условия; неясное прикрепление исключения; срок без точки отсчёта; обязанность без определимого обязанного лица; конкурирующие толкования из-за координации/модификаторов.

Обычно `REVIEW`; повышать только если противоречие или неразрешимая ссылка механически доказуемы.

## LDB-006 — Preserve established professional terminology

Source locators: `BOOK-ABRAMOVA-2017`, p. 130; `BOOK-MOTYAKINA-LOPATIN-2016`, around p. 20.  
Scope: legal/official documents  
Basis: `PROJECT_REFINED`  
Level: term/document  
Confidence: high

Предпочитать установленные профессиональные термины и формулы там, где они несут предметный смысл. Общая борьба с повторами не должна заменять их приблизительными синонимами.

Это не запрещает исправлять реально неверный юридический термин.

## LDB-007 — Structural hierarchy is semantic, not decorative

Source locator: `BOOK-ABRAMOVA-2017`, pp. 129–130.  
Scope: legal documents  
Basis: `SOURCE_DIRECT` + `PROJECT_REFINED`  
Level: document  
Confidence: medium-high

Если жанр различает функциональные части, структура должна сохранять их роли и помогать отличать основания, предписания, права, обязанности, выводы, требования и другие функции.

Не придумывать иерархию только ради более официального вида.

## LDB-008 — Directive modality must match the legal function

Source locator: `BOOK-BEGLOVA-2019`, p. 144 onward.  
Scope: normative / official-admin  
Basis: `PROJECT_REFINED`  
Level: clause  
Confidence: medium-high

Различать минимум:

- обязанность;
- запрет;
- разрешение/право;
- рекомендацию;
- фактическое утверждение.

Не перефразировать один класс в другой при редактуре. Лексикон модальности можно использовать как диагностическую подсказку, но не выводить юридическую силу из одного токена.

## LDB-009 — Avoid vague references where exactness is required

Source locator: `BOOK-MARYEVA-2015-2`, p. 122.  
Scope: legal/official documents  
Basis: `PROJECT_REFINED`  
Level: phrase  
Confidence: high

Относительные даты, неназванные документы, расплывчатые количества и неясные референты — кандидаты на проверку, если документ требует проверяемой точности.

Относительная формулировка не ошибочна, если точка отсчёта однозначна и стабильна в контексте.

## LDB-010 — Direct word order is a register prior, not a hard grammar rule

Source locator: `BOOK-NOVOSELTSEVA-2018`, p. 8.  
Scope: official-business prose  
Basis: `PROJECT_REFINED`  
Level: sentence  
Confidence: medium

Источник описывает прямой порядок слов как характерный для официально-делового синтаксиса ради логической последовательности и точности.

Не превращать это в `SVO required`. Использовать только как слабый prior, если маркированный порядок создаёт двусмысленность или скрывает юридическую связь.

## LDB-011 — Formal requirements in old books are historical until revalidated

Source: corpus-wide project rule.  
Scope: formal/document layout  
Basis: `PROJECT_DERIVED`  
Level: source governance  
Confidence: high

Книга до 2025 года может быть ценной для языка и жанра, но не активирует современное правило оформления/реквизита сама по себе.

Сверять с ГОСТ Р 7.0.97-2025, актуальными правилами Росархива и другими применимыми текущими источниками.
