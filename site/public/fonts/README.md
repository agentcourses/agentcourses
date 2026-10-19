# Fonts

These font files are served from this site, so pages make no third-party font request. Each family is licensed under the SIL Open Font License 1.1, whose full text sits beside the files. The site's own material is Apache-2.0; these fonts keep their own licence.

| File | Family, weights | Source package | Path in package |
|---|---|---|---|
| `IBMPlexSans-Regular-Latin1.woff2` | IBM Plex Sans 400 | `@ibm/plex-sans@1.1.0` | `fonts/split/woff2/` |
| `IBMPlexSans-Medium-Latin1.woff2` | IBM Plex Sans 500 | `@ibm/plex-sans@1.1.0` | `fonts/split/woff2/` |
| `IBMPlexSans-SemiBold-Latin1.woff2` | IBM Plex Sans 600 | `@ibm/plex-sans@1.1.0` | `fonts/split/woff2/` |
| `IBMPlexMono-Regular-Latin1.woff2` | IBM Plex Mono 400 | `@ibm/plex-mono@2.5.0` | `fonts/split/woff2/` |
| `IBMPlexMono-Medium-Latin1.woff2` | IBM Plex Mono 500 | `@ibm/plex-mono@2.5.0` | `fonts/split/woff2/` |
| `source-serif-4-latin-opsz-normal.woff2` | Source Serif 4, variable weight 200–900 and optical size 8–60 | `@fontsource-variable/source-serif-4@5.3.1` | `files/` |

## Licences

- `LICENSE-IBM-Plex.txt` is `LICENSE.txt` from both IBM packages; the two files are identical. Copyright © 2017 IBM Corp., with Reserved Font Name "Plex". It keeps the upstream bytes, including Windows line endings.
- `LICENSE-Source-Serif-4.txt` is `LICENSE.md` from the upstream `adobe-fonts/source-serif` repository, `release` branch. Copyright 2014–2023 Adobe, with Reserved Font Name ‘Source’. The Fontsource package builds its files from the Google Fonts release of the same family.

## How the files were obtained

Each package tarball was downloaded directly from the npm registry and checked against the registry's published integrity value before extraction. The packages were never installed, so no package script ran. The IBM packages declare an install-time telemetry script; extracting files from the tarball avoids it, and the site loads no telemetry.

| Tarball | Registry integrity |
|---|---|
| `https://registry.npmjs.org/@ibm/plex-sans/-/plex-sans-1.1.0.tgz` | `sha512-WPgvO6Yfj2w5YbhyAr1tv95RUz4LRJlqN+CmYvBglabXteufP1D1E9BABMde+ZIKdRbFJDoKF5eQzfhpnbgZcQ==` |
| `https://registry.npmjs.org/@ibm/plex-mono/-/plex-mono-2.5.0.tgz` | `sha512-STBJIPxPomOYPmBMO7z5TKPJUotAF9u3gAUumTqVgwgrAO+K4FRNh0MlhsoJjKhJKsMbBJR10/bk4inkj/wc1w==` |
| `https://registry.npmjs.org/@fontsource-variable/source-serif-4/-/source-serif-4-5.3.1.tgz` | `sha512-4Rtay22SC4lMvw11r/+9kxANB6P3M0X8s1NudBC2v0J1KU2y3DcMoNcT3lBoZ/CqLirzf+StlO6UlJilyrvaUg==` |

SHA-256 of each copied file:

```text
b5ad7bd39f996144915f0ad9849a90183b27d8c28ad97ed98af5b1bebc51f6b1  IBMPlexSans-Regular-Latin1.woff2
b5610af04d0d4b5a14a621d96d974b993e945a065db1a8861918f69ef9321934  IBMPlexSans-Medium-Latin1.woff2
fff0ab3a88b0b4aa0b693e4f0201359a15183b08e3fa5696d1918d8f0ade8ad5  IBMPlexSans-SemiBold-Latin1.woff2
e8993d946649b9d01abb1ed06d574b19d8ea3e66b5c3948602db335c44c18e56  IBMPlexMono-Regular-Latin1.woff2
41201b658a328b9d00368215c2f1102770f80b15952ab82631e4006255e6365d  IBMPlexMono-Medium-Latin1.woff2
f2ea9c12d2fe9bd3a9589b02ad2c0909da88f30938c91adc838c4f4098f9f9e0  source-serif-4-latin-opsz-normal.woff2
7e6b2818edbd8f6a01ae80641cc8f16a51080d08fb4e532be3a0b6f74adb07da  LICENSE-IBM-Plex.txt
c21d7293d87b6d7ab1d0229a2f55b77f33a7613a6a4e66f6693d68d7d8d09464  LICENSE-Source-Serif-4.txt
```

The Latin subsets cover Basic Latin, Latin-1 and common punctuation. Each `@font-face` rule repeats its package's `unicode-range`, so other characters fall back to system fonts.
