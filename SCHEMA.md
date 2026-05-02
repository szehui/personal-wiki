---
title: Wiki Schema
---

# Wiki Schema

## Architecture: Multi-Domain Extensible
This wiki is a unified knowledge base supporting multiple intersecting domains. To support cross-pollination, the folder structure remains flat (entities/, concepts/), while domains are tracked via YAML frontmatter.

**Active Domains:**
- personal-knowledge
- work-knowledge

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., transformer-architecture.md)
- Every wiki page starts with YAML frontmatter
- Use [[wikilinks]] to link between pages (minimum 2 outbound links per page)
- When updating a page, bump the updated date
- Add every new page to index.md
- Append every action to log.md
- Provenance markers: On pages that synthesize 3+ sources, append ^[raw/articles/source-file.md] at the end of paragraphs whose claims come from a specific source.

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
domains: [domain1, domain2]  # multi-domain tracking
tags: [from taxonomy below]
sources: [raw/articles/source-name.md]
confidence: high | medium | low
contested: true
contradictions: [other-page-slug]
---
```

### raw/ Frontmatter
```yaml
---
source_url: https://example.com/article
ingested: YYYY-MM-DD
sha256: <hex digest of the body>
---
```

## Tag Taxonomy

### Universal Tags (Cross-Domain)
- person, organization, product, book, article, methodology, framework
- comparison, timeline, controversy, prediction

### Domain-Specific Tags

Domain: personal-knowledge
- travel, bike, fitness, health, family, homelab

Domain: work-knowledge
- contacts, companies, medical-knowledge, nemt-industry

## Page Thresholds
- Create a page when an entity/concept appears in 2+ sources OR is central to one source
- Add to existing page when a source mentions something already covered
- Split a page when it exceeds ~200 lines
- Archive a page when content is superseded (move to _archive/)

## Update Policy
When new information conflicts with existing content:
1) Check dates — newer sources generally supersede older ones
2) If genuinely contradictory, note both positions
3) Mark contradictions in frontmatter: contradictions: [page-name]
4) Surface for user review in lint/report
