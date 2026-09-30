# ארכיטקטורת המערכת - טיוטה 0.1

## מטרת המסמך

המסמך מגדיר את ארכיטקטורת היעד של סביבת המחקר הדיגיטלית ל-*Protocols of the Elders of Zion*. גרסה 2.1 של האתר היא עדיין גרסה זמנית המבוססת בעיקר על מהדורת Cesare G. De Michelis, אך היא צריכה להיות היישום הראשון של הארכיטקטורה הסופית ולא ענף פיתוח נפרד.

הארכיטקטורה נועדה לשרת את מטרות המחקר של סברינה: חקר תהליכי **rewrite / editorship**, זיהוי שכבות ומקטעים בעלי קול עריכתי שונה, השוואה בין עדי נוסח בעלי ארגון לא-מקביל, וקישור עתידי של ה-*Protocols* לכתבי Sharapov, Boutmy, Efron, Tsion ואחרים. היא אינה מניחה שקיים נוסח יחיד וסופי שעליו כל המערכת נשענת.

## 1. עקרונות יסוד

### 1.1 הפרדה בין יצירה, עד, ושחזור

יש להבחין בין:

- **Work** - היצירה המופשטת שאנו מכנים *Protocols*.
- **Witness** - מסמך היסטורי ממשי: מהדורה, חוברת, פרסום עיתונאי או כתב יד.
- **Reconstruction** - טקסט מודרני משוחזר, כגון הנוסח של De Michelis.
- **Derived provisional witness** - שחזור זמני של עד שנוצר מתוך ה-apparatus של De Michelis. זהו כלי עבודה בלבד ואינו שקול לתעתיק של העד ההיסטורי.
- **Hypothetical textual stage** - שלב משוער במסירה, כגון W/X/Y/Z אצל De Michelis או שלב שיוצע במסגרת המחקר של סברינה.

ממשק המשתמש חייב להציג את ההבדלים הללו במפורש.

### 1.2 אין יחידת מספור אוניברסלית

"Protocol XII" אינו מזהה קנוני, משום שהעדים מחלקים את הרצף ל-22, 24 או 27 יחידות. יש להשתמש ב-ID נייטרלי של locus/segment ולשמור את המספור של כל עד כמאפיין שלו.

### 1.3 כל שכבה ניתנת להחלפה

הזנת עדי הנוסח המצולמים בעתיד לא אמורה לשנות את ה-UI או את הקישורים. `A2-provisional` יוחלף ב-`A2-documentary`, תוך שמירת זהות העד, היישויות, ה-alignment והקישורים ככל האפשר.

### 1.4 provenance הוא נתון מחקרי

לכל טקסט ולכל קריאה צריך להיות ברור מאין הגיעו. בפרט, הנוסח של De Michelis חייב להבחין בין:

- חומר המעיד K;
- חומר שבו K קיים אך De Michelis משלים/מתקן אותו באמצעות עדים אחרים;
- חומר שאינו מעיד K ומובא משחזור המבוסס על עדים אחרים.

בגרסה 2.1 ההבחנה מיוצגת גם ברמת span: K-attested / supplied-not-in-K / differs-from-K, על בסיס alignment מול K הזמני המשוחזר מן ה-apparatus. זהו provenance זמני עד לקליטת K הדוקומנטרי.

### 1.5 מבנה הוא ראיה

גבול בין Protocols, פסקאות, paratext והערות מקור הוא חלק מן העדות הטקסטואלית. אין "ליישר" מבנים שונים כדי ליצור סינופסיס נוח.

### 1.6 שלוש מערכות הערות נפרדות

ב-De Michelis יש לפחות שלוש שכבות שיש לקודד בנפרד:

1. **critical apparatus** - ההערות המספריות המשוות עדים;
2. **source notes** - הערות היסטוריות של הטקסט עצמו המסומנות `(*)`, `(**)` וכו';
3. **source parallels** - אותיות לטיניות בסוגריים המקשרות ל-Joly.

בממשק ברירת המחדל source notes הן חלק מן הקריאה; critical apparatus ו-Joly הן שכבות שניתן לפתוח לפי צורך.

## 2. מודל הישויות המרכזי

| ישות | תפקיד | ID מוצע |
|---|---|---|
| Work | היצירה המופשטת | `work.protocols` |
| Document | אובייקט ביבליוגרפי/פיזי | `doc.k.1903.znamia` |
| Witness | עד טקסטואלי | `wit.K` |
| Reconstruction | שחזור מודרני | `rec.demichelis` |
| StructuralUnit | יחידה לפי עד | `wit.A1.protocol.17` |
| Locus | אזור נייטרלי ברצף הטקסטואלי | `loc.000123` |
| Reading | קריאה של עד ב-locus | `rdg.loc000123.A1` |
| Note | הערה היסטורית/עריכתית | `note.source.II.01` |
| ApparatusItem | הערת apparatus | `app.dm.0351` |
| Alignment | קשר בין loci/טקסטים | `align.00045` |
| SourceParallel | מקבילה ל-Joly/Sharapov וכו' | `srcpar.00045` |
| Entity | אדם/מקום/ארגון/חיבור | `person.sharapov` |
| Concept | קטגוריה אנליטית | `concept.gold-standard` |
| Hypothesis | מודל מסירה או ייחוס | `hyp.demichelis`, `hyp.sabrina.01` |

## 3. שכבות הנתונים

### 3.1 שכבה קנונית: TEI P5

TEI הוא מקור האמת המחקרי. האתר אינו מקור האמת אלא projection.

מבנה יעד:

```text
tei/
  corpus.xml
  texts/
    reconstructions/
      demichelis.xml
    witnesses/
      K.xml
      A1.xml
      A2.xml
      N.xml
      B.xml
  annotations/
    source-notes.xml
    source-parallels.xml
    apparatus.xml
    alignments.xml
    ner.xml
    concepts.xml
  authorities/
    witnesses.xml
    persons.xml
    places.xml
    organizations.xml
    works.xml
    bibliography.xml
  models/
    transmission-demichelis.xml
    transmission-sabrina.xml
  schema/
    protocols.odd
    protocols.sch
```

בגרסה 2.1 חלק מן הקבצים עדיין נמצאים במבנה legacy של 1.x, אך `architecture-manifest.json` מצהיר על תפקידם ומאפשר migration הדרגתי.

### 3.2 שכבת web projection

JSON/JavaScript שנוצר מן-TEI ומיועד לחיפוש, סינופסיס וויזואליזציה. הוא בר-מחיקה ובר-בנייה מחדש.

### 3.3 שכבת audit

כל שינוי אוטומטי או הכרעה מחקרית נשמרים עם provenance, confidence, תאריך ושיטה. אין להסתיר חוסר ודאות באמצעות טקסט "נקי".

## 4. מבנה לא-מקביל וסינופסיס

הסינופסיס מבוסס על שני מושגים נפרדים:

- **basis structure** - איזה עד קובע את שורות התצוגה;
- **visible witnesses** - אילו עדים מוצגים ובאיזה סדר.

כל witness שומר את גבולות היחידות שלו גם כאשר הוא מוקרן לתוך structure של עד אחר. ה-alignment אינו מבוסס על מספר Protocol אלא על loci/anchors.

## 5. De Michelis כבסיס זמני

בשלב הנוכחי De Michelis מספק:

- reconstructed reference text;
- apparatus;
- provisional witness reconstructions;
- Joly alignment;
- מידע על מבנים ויחסי מסירה.

סטטוס העדים K/A1/A2/N/B באתר 2.1 הוא **provisional - derived from De Michelis apparatus**. הם מיועדים לפיתוח הכלים ולבדיקות ראשוניות, לא כתחליף לתעתיקים מן העדים עצמם.

כאשר ייקלטו ה-PDFs/סריקות של העדים:

1. כל witness יקבל diplomatic transcription עצמאי;
2. תיווצר שכבת normalized text נפרדת;
3. יתבצע alignment מול loci הקיימים;
4. ה-provisional reconstruction יישמר כגרסה היסטורית/audit ולא יוצג כברירת מחדל;
5. הסינופסיס, החיפוש, NER והדיאגרמות יעברו אוטומטית לטקסט הדוקומנטרי.

## 6. הערות מקור והערות De Michelis

### Source notes (`*`, `**` וכו')

- נשאר marker במקומו בטקסט;
- תוכן ההערה מוצא מזרם הקריאה;
- ההערה נפתחת בפאנל/חלונית;
- היא מקבלת `type="source-note"` ו-provenance לעד/שחזור שבו היא מעידה.

### Critical apparatus (מספרים)

- נשמר במלואו;
- מוסתר כברירת מחדל בקריאה;
- משמש כרגע לבניית העדים הזמניים;
- בעתיד ישמש להשוואה ל-collation העצמאי שלנו.

### Joly parallels (אותיות)

- נשמרים כ-source-parallel;
- אינם מגדירים עוד את החלוקה הפנימית העיקרית של הטקסט;
- בעתיד אותה תשתית תשרת גם מקבילות ל-Sharapov, Boutmy, Efron, Tsion וכו'.

## 7. ישויות, concepts וקריאה מרחוק

NER הוא שכבת annotation ולא חלק מן הטקסט. לכל mention יש:

- authority ID;
- witness/reconstruction;
- locus/structural unit;
- span;
- provenance/method.

יש להבחין בין named entities לבין concepts. השכבה האנליטית העתידית צריכה לתמוך במיוחד בשדות כלכליים ופוליטיים הרלוונטיים להצעת המחקר: gold standard, currency, credit, banks, capital, debt, autocracy, liberalism, agriculture, revolution ועוד.

כל visualization של distant reading חייב להיות reversible: לחיצה על node/cell מחזירה למופעים בטקסט.

## 8. מודלים מתחרים של מסירה

אין `relations.xml` יחיד שמוצג כאמת סופית. יש מודלים מזוהים:

- `hyp.demichelis` - המודל של De Michelis;
- `hyp.sabrina.*` - מודלים שיוגדרו במחקר;
- בעתיד מודלים נוספים.

כל edge מקבל `type`, `certainty`, `resp`, `evidence` ו-status כגון documented / inferred / hypothetical.

## 9. שאלות פתוחות שאינן חוסמות את v2

1. זיהוי מדויק של Sharapov/A2 במודל המסירה העתידי.
2. רשימת העדים הסופית שייכללו במהדורה.
3. ontology סופי של concepts.
4. מידת הנרמול הלשוני ברובד normalized.
5. האם source notes יוצגו כברירת מחדל בפאנל צד, popover או בשתי הצורות.
6. segmentation פרשני של שכבות/קולות מחבריים.

העיקרון: אף אחת מן השאלות הללו אינה צריכה לחייב שינוי ב-ID model או בממשק הבסיסי.

## 10. היקף גרסה 2.1 הזמנית

גרסה 2.1 נועדה להוכיח שהארכיטקטורה עובדת עם הנתונים שכבר בידינו. היא כוללת:

- הגדרה מפורשת של De Michelis כ-reconstruction/reference;
- סימון כל K/A1/A2/N/B כ-provisional derived witnesses;
- הפרדה ראשונה של source notes מן הטקסט הרציף;
- תצוגת provenance/status בקריאה;
- הצגת מפת De Michelis כמודל מחקרי מזוהה, לא כ-stemma סופי;
- שמירת כל יכולות 1.1: synopsis, search, entities, distant reading, TEI download, guide;
- manifest שמגדיר את תפקידי הקבצים לקראת migration לעדים הישירים.

גרסה 2.1 **אינה** מנסה לפתור כעת את ה-stemma של סברינה או להחליף את העדים הזמניים בתעתיקים מן הסריקות.

## 11. מבחני קבלה לגרסאות הבאות

- ניתן להחליף witness provisional ב-documentary בלי לשנות route או ID של העד.
- source note אינה מופיעה כחלק מן ה-running text.
- לכל תצוגת comparison ידוע מהו basis structure.
- לכל קריאה/שחזור ידוע provenance.
- כל distant-reading view מקשר חזרה ל-locus.
- כמה transmission hypotheses יכולים להתקיים זה לצד זה.
- TEI ניתן לבנייה מחדש ל-web projection ללא מידע מחקרי שמוחזק רק ב-JavaScript.


## Implemented in 2.1
- Verified asterisk-source-note layer (exhaustive for De Michelis Appendix).
- Reconstructed-text segmentation driven by printed headings rather than apparatus-anchor positions.
- Provisional span-level K provenance in `tei/analysis/reconstruction_provenance.xml` and `research/reconstruction_span_provenance.json`.


## 2.2 implementation: canonical loci, documentary witnesses, research annotations

### Canonical locus layer
The edition now defines a witness-independent sequence of canonical loci (`L0001` …) from the intervals between De Michelis apparatus anchors. A locus is **not** a protocol number. Each locus maps separately to the structural unit that contains it in each current witness view. The full map is in `research/canonical_loci.json` and the TEI stand-off representation in `tei/analysis/canonical_loci.xml`. Future documentary transcriptions should insert locus anchors only after human alignment; the locus IDs remain stable even when witness segmentation changes.

### Documentary witness contract
New witnesses are expected to enter the system as diplomatic TEI, preserving source pagination and lineation, historical source notes, uncertain readings, additions/deletions, and optional normalization through TEI `choice`. The contract is documented by `tei/templates/documentary-witness-template.xml`, validated by `tei/schema/documentary-witness.rng`, and checked with `scripts/validate_documentary_witness.py`.

### Research annotations
Interpretive claims are intentionally separate from transcription and textual apparatus. Researchers may annotate selected passages with a controlled but extensible vocabulary (economic discourse, gold standard, utopian/dystopian register, possible Sharapov/Boutmy relations, editorial voice, rhetorical figure, etc.). Browser-created annotations are local-first and exportable; the TEI stand-off target is `tei/analysis/research_annotations.xml`. This prevents provisional interpretation from being silently encoded as documentary fact.
