# Sprint1 Audit

Scope: tracked files only. Excluded experimental/deep_mining/** as requested.

## Summary
- The top 30 largest tracked files are all npm cache artifacts under `motherload_projet/client/.npm-cache/`. These should not be versioned.
- Several generated logs and test outputs are tracked and should be ignored to avoid churn.
- No exact duplicate files were found in `docs/`, `inputs/`, or `app/`.

## Top 30 Largest Tracked Files
| Rank | Size | Bytes | Path |
| --- | --- | --- | --- |
| 1 | 69.2 MB | 72513352 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/8f/ce/e8d23e8ba8f2f7411afcca277a73e4ede600bbc4d7d8a3ab90210928ac00ba32979ac95319ac40f32a6249fc796fec49ce4296919b9de4ea4b43619c81eb` |
| 2 | 36.9 MB | 38711951 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/7e/ee/a99955fece8e4ff99155ba0fd3e163e8965f54c92468f13fd2c9d28b545cd9721ffed41f999d5eff496c8a217eb942d1c1bc98d663d79bff530391e3fa18` |
| 3 | 36.9 MB | 38706452 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/09/2b/ceb5791edc787ab02fba42c6742e648a98ec932a5ee29f3a940e4def18d4a4f76f35cbccebc4c945c1a5b559578fd56845d61c445072dec6ae248c271fd5` |
| 4 | 10.3 MB | 10819254 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/64/1f/fd5501632fa2b8a432d9e509a8a60df15d714c31dff4b40d2ba64e1210a1a8bfe098d41135b8a46b8b5fc54b5fdb69e26821c62dc192df46789e10818684` |
| 5 | 10.3 MB | 10808539 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/84/47/09c22b579d55276018a9feae280cca2af853a38980e8b0077fe7efb1c72bd6e808fbf44d2f087955a73bcff0dbfbc48a0e042027c7527e4c16a03df60d88` |
| 6 | 9.7 MB | 10142604 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/5f/66/dd23f9bdf807ba76b96ac274180974fb6bd858b29066e55001aacb132025494ea1fb75b814df384c4774580cab4b9bcba9941e26ba22cad6258c0e8b1f20` |
| 7 | 9.6 MB | 10027220 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/f7/04/f9fb54ba306b61fef730743a5ec42c8dc9a6e79d485aebad7a8056122527d269a2109d47b2965d0f0f054dea64036070dfe83aca4389a70bf39dcc3d1dfc` |
| 8 | 9.4 MB | 9856190 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/6d/8e/91c1bedab8907572019bc3fe055fd8c756ff791133ec5caaf36a2aa6a854d40dbad7975ed96946e20c4508fb02031bc289a0184980485e12dbb15b60d815` |
| 9 | 8.7 MB | 9141554 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/6c/ed/f2d7462292e53052e0d441133829fc0d90a867a553bb20f75bb2b7a3c0df7f000049cf34d0e06787c32ccd4ab54efad107dff369db9e5adec559a590e3be` |
| 10 | 8.1 MB | 8526345 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/fe/75/12ab5b7b3d26a4bfbee73fac9392ebfa434e86f28abc9c0cf7ac21d2b4ed8f08565bea9547b4b273c6c1210f8b60c066e7f2a80c4ad628ea5d54903c6463` |
| 11 | 8.1 MB | 8512812 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/20/a9/2a9d975df61492b2f8d34ba5be3fc02bf01a9d698648f5ed974b2db12e01532d430ba36fc978878ad770fde1562c3a830173e9b7ed9da5a1ed0ad7a907f6` |
| 12 | 6.7 MB | 7077548 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/f5/b6/76020aa72251110dddfbd6de774e3d3ef0d6204fe7ac66ee619f415d12fe6db694cdd75d8c7fad3a7f0c69fb2be74313568654764e588a0283f4d50bb577` |
| 13 | 6.2 MB | 6450749 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/74/59/7e7771f463fae43505df597322a37c0b2cf484bd5f096dfe53a313d650d3dd944ab80336f38e52f304d9816cae1bd61d2acec110bec369427383f92f3452` |
| 14 | 6.1 MB | 6442854 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/4a/04/91675e2cb888fa160273869a5749b17b777e246ed75c471d49e622b145f22119d1b0be9fb2d6f7c5efe3ee78edc3211be2f92ba03a55948496d766a22afc` |
| 15 | 5.9 MB | 6149132 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/80/ad/29769b3d5d4c6066af6d45184e04e0d41148d9bc3ca73fd6e3eedb2a32e902cd4ef349b3ceac4b89653e7bb58586f367d15fc491a8dcd787bea6abfc7c1e` |
| 16 | 5.8 MB | 6086736 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/b8/2a/f020c0f62572d5643da6ba2ebb69b583860ee0ed1dc25602ef8bd22970e85dd238ab4cc49c9f74b77e4f38b6c67a983b5eab29477b1270086917322ea999` |
| 17 | 5.4 MB | 5625880 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/ba/44/cf561a86e2337332ba36a80f4748249254937768deed95bfa17ea602b77111d325aba1e036551dfc30dace1cb43f7158fe0da20c69dd24142b565a8c21fc` |
| 18 | 5.1 MB | 5352657 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/f3/54/7dccf6ae0d0561a2c4ea669519811d543a5e3177c69ee2fd3607ffff96cfd9e14cf80ebb6e97823fd8d4c7f7af44cd8d076c81e27640c0d4706168664d73` |
| 19 | 5.0 MB | 5218910 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/dc/80/ef544bb947945bbc9baf1f564b7735093f28b5680e25c24b257d090c0b9c6309588e7912cc0d774e1fd11292aabee904f8266aa7e4da132fe5e7159ba881` |
| 20 | 4.5 MB | 4716236 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/c4/92/ddb58fcff4e40b71160036b4a620f98e62435fdc762bb728adc9e28dfbc345d21904d022f8203e80024ecb4e1739e29d112db898f06d8731b56b7b67cc02` |
| 21 | 4.2 MB | 4453338 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/1f/f8/2060c53e683fbccf9ef503cec87ad204766ecc51a418fcae3329931dc5836eb463928de292ccdf32a72c18b5b975ab4bfd8b669d81f0926d94a1f2cb169c` |
| 22 | 4.2 MB | 4355343 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/75/ab/c20f665cf349f30d54705d37103ffdbc7e225b70ec2f76894bd2c3a23ac6f005aef691e826554d16ae1d4c62b6ee08bf7c3a6a7975585015644a47664096` |
| 23 | 3.8 MB | 4000380 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/9e/0f/f6c1e3d303f0fc0af3630664474758f38c9844ea3c0510b3dafb6f7c25b4341c118a3d4be1f12fc1b6cbc2367f9d5efcd40c874c497a1ce7ec4e67e18104` |
| 24 | 3.6 MB | 3799160 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/3e/71/b935ee48fb1a9ae30ebd3154bced15313f6ab4efd4746f4cafcea031fb04b01dea3d4de9ed038302a96fb9faaa1e24f24d7172299b5a9f4ff7d92920fe12` |
| 25 | 3.6 MB | 3771757 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/fc/df/dae750bd85425bac3ea74d8a6b3211ab0bcb39f702a95dd9e3c0058f4069a318a1b6281f3c21954c5f4b3c97011c977bb8d90792fd82d0121dcfffeb7e21` |
| 26 | 3.3 MB | 3489329 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/a9/da/cc80fdf4cf5775f08a0bad130aa414b5d7ac6d515239127103b75c178823a49560d08c2b255c97a224975e84ff1ebdf5a28ba3d788cad4e59e1ff2436a9a` |
| 27 | 3.2 MB | 3351978 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/f1/d5/cf076188e1d23c8d5e0c8140c605e2dd1a4f1e91fa9567405d2dcad1ce8706806ef996d3449964be804eeea24285ff4a1252e7333434fe83d845276dc590` |
| 28 | 3.1 MB | 3285103 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/ca/54/dc0c904ddc7a76d53761453e7304e222ef73fafd6d2ac2f945124db67e4757721b4d4ce53841cdfb4a4cd5f84298c4ba2e67a3382c6f4d7d9d6a92184158` |
| 29 | 3.0 MB | 3151268 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/1d/07/50d019675f77232503f641acc41a0d5da0a6204b1db3eb34be97609d238643e80ca0372575e2ec832bdacb6719e2e13e078f3611ae4589f5c022ac6f53d0` |
| 30 | 2.6 MB | 2739389 | `motherload_projet/client/.npm-cache/_cacache/content-v2/sha512/ac/fb/a083ac26782f74eb3f3c24a79a70620f5ef6f051da7b67fd5f113abd7cbc18ef8275615d98ed3f09b8ca8a92e0713b547ed0af2ede555885cb18c59dd459` |

## Generated Files and Dirs to Ignore (Tracked Now)
| Item | Why it looks generated | Recommendation |
| --- | --- | --- |
| `motherload_projet/client/.npm-cache/` | npm cache artifacts | Remove from git index and keep ignored. |
| `motherload_projet/.npm-cache/` | npm cache artifacts | Remove from git index and keep ignored. |
| `mining_errors.log` | runtime log | Ignore. Remove from git if not needed. |
| `mining_integration_test_report.json` | test output | Ignore. Regenerate in CI or on demand. |
| `mining_integration_test_report.txt` | test output | Ignore. Regenerate in CI or on demand. |
| `/outputs/` | generated outputs | Ignore. Keep `.gitkeep` only if the folder must exist. |
| `/logs/` | generated logs | Ignore. |
| `/temp_test_lib/` | test artifacts (PDFs, reports) | Ignore. |
| `/test_mining_output/` | test artifacts | Ignore. |
| `/test_crawler_biorxiv/` | test artifacts | Ignore. |
| `/test_direct_download.pdf` | generated test download | Ignore or move to `tests/fixtures/` if it is a permanent fixture. |
| `/motherload_projet/data/librarium.db` | local DB file | If it is seed data, move to LFS. Otherwise ignore and regenerate. |

## Exact Duplicates (SHA256) in docs/, inputs/, app/
No exact duplicates found.

## .gitignore Updates Applied
- `node_modules/`
- `.npm-cache/`
- `npm-debug.log*`
- `pnpm-debug.log*`
- `yarn-debug.log*`
- `yarn-error.log*`
- `*.log`
- `mining_integration_test_report.*`
- `/outputs/`
- `/logs/`
- `/temp_test_lib/`
- `/test_mining_output/`
- `/test_crawler_biorxiv/`
- `/test_direct_download.pdf`
- `/motherload_projet/data/librarium.db`
- `.DS_Store`

## Suggested Follow-ups
- Remove tracked npm cache files from the index to stop them from shipping with the repo.
- Decide whether `librarium.db` is canonical seed data or local state, then either move it to LFS or keep it ignored.
- If `test_direct_download.pdf` is a fixture, move it under `tests/fixtures/` and keep it tracked there.
