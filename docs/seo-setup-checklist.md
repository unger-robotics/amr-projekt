---
description: >-
  Checkliste fuer Google Search Console, Sitemap-Einreichung
  und SEO-Verifizierung.
robots: noindex, nofollow
---

# SEO Setup Checklist (intern)

Diese Datei ist NICHT in der Navigation – sie dient als interne Referenz.

## Google Search Console

1. [x] Property hinzugefuegt: `https://unger-robotics.github.io/amr-projekt/`
2. [x] Verifikation: HTML-Datei (`googleac48f43e9ebd9a9e.html`) im `docs/`-Verzeichnis
3. [ ] Sitemap einreichen: `sitemap.xml` unter Sitemaps hinzufuegen
4. [ ] URL-Pruefung: Startseite manuell indexieren lassen
5. [ ] Abdeckungsbericht pruefen (nach 1-2 Wochen)

## Bing Webmaster Tools (optional)

1. [ ] https://www.bing.com/webmasters oeffnen
2. [ ] Import aus Google Search Console moeglich
3. [ ] Sitemap einreichen

## Pruefung nach 1-2 Wochen

- [ ] `site:unger-robotics.github.io/amr-projekt` in Google suchen
- [ ] Mindestens Startseite indexiert?
- [ ] Search Console: Abdeckungsbericht pruefen
- [ ] OG-Vorschau testen: https://www.opengraph.xyz/

## Technische Pruefpunkte

```bash
# Sitemap erreichbar?
curl -s -o /dev/null -w "%{http_code}" https://unger-robotics.github.io/amr-projekt/sitemap.xml

# robots.txt erreichbar?
curl -s https://unger-robotics.github.io/amr-projekt/robots.txt

# Meta-Tags im HTML?
curl -s https://unger-robotics.github.io/amr-projekt/ | grep -iE '(og:title|og:description|description|keywords)'

# GitHub-Repo-Metadaten?
gh repo view unger-robotics/amr-projekt --json description,homepageUrl,repositoryTopics
```
