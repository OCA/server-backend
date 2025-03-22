The list of fictional characters was generated from [wikidata.org](https://query.wikidata.org) using query:

```
SELECT ?item ?itemLabel WHERE {
    ?item (p:P31/ps:P31/(wdt:P279*)) wd:Q95074.
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```
