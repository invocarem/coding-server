You are an expert Swift code formatter.
Your task is to count **exactly how many strings** appear in the given Swift array and renumber them sequentially, and provide updated array

### RULES

1. Do not generate or wrap the result in a Swift function.
2. Do not merge or split any string in the array.
3. Ignore any existing /* number */ comment -- they may be incorrect.
4. Ignore period `.`, semicolons `;` or punctuation inside strings.
5. Ignore blank lines -- they do not count as items
6, Count one string for each element ending with a double quote (") followed by a comma (,).
7. Also count one string for the final element that ends with a double quote (") followed by `]`.
8. Every string in the output must begin with a renumbered /* number */ as 
```
/* N */ "string text",

9. Preserve original indentation, spacing, and commas.
10. No explanations, notes, but markdown code block only.

### EXAMPLE
** INPUT **
private let text = [
  /* 1 */ "string a",
   "string b",
  /* 2 */ "string c",
]


** Expected OUTPUT **

```swift
private let text = [
  /* 1 */ "string a",
  /* 2 */ "string b",
  /* 3 */ "string c",
]

** NOTE **
In the output, every string starts with a /* number */ comment

### Now, process this input

```swift
private let text = [
/* 1 */ "Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.",
/* 2 */ "Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis.",
/* 3 */ "Verumtamen Deus confringet capita inimicorum suorum, verticem capilli perambulantium in delictis suis.",
/* 4 */ "Dixit Dominus: Ex Basan convertam, convertam in profundum maris.",
/* 5 */ "Ut intingatur pes tuus in sanguine; lingua canum tuorum ex inimicis ab ipso.",
/* 6 */ "Viderunt ingressus tuos, Deus, ingressus Dei mei, regis mei, qui est in sancto.",
/* 7 */ "Praevenerunt principes conjuncti psallentibus, in medio juvencularum tympanistriarum.",
/* 8 */ "In ecclesiis benedicite Deo Domino, de fontibus Israel.",
/* 9 */ "Ibi Benjamin adolescentulus, in mentis excessu; ",
"principes Juda, duces eorum; principes Zabulon, principes Nephthali.",
/* 10 */ "Manda, Deus, virtuti tuae; confirma hoc, Deus, quod operatus es in nobis.",
/* 11 */ "A templo tuo in Ierusalem, tibi offerent reges munera.",
/* 12 */ "Increpa feras arundinis; congregatio taurorum in vaccis populorum, ut excludantur qui probati sunt argento;",
" Dissipa gentes quae bella volunt. Venient legati ex Aegypto; Aethiopia praeveniet manus eius Deo.",
/* 14 */ "Regna terrae, cantate Deo; psallite Domino.",
/* 15 */ "Psallite Deo, qui ascendit super caelum caeli ad orientem; ",
"ecce dabit voci suae vocem virtutis. Date gloriam Deo super Israel; magnificentia eius et virtus eius in nubibus.",
/* 17 */ "Mirabilis Deus in sanctis suis; Deus Israel, ipse dabit virtutem et fortitudinem plebi suae; benedictus Deus."
]

