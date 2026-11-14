# 대전 캐시백 주유 지도 (PWA + Android APK)

대전 지역화폐 **온통대전(대전사랑카드)** 캐시백 제공 주유소·LPG충전소 **82곳**의 유가와 캐시백 체감가를 비교하는 모바일 앱입니다.

## 구조
- `docs/`: 설치형 웹앱(PWA) 정적 파일 (`index.html`, `manifest.webmanifest`, `sw.js`, `data/stations.json`, `icons/`)
- `android/`: Android APK 네이티브 WebView 래퍼 프로젝트 (위치 권한·카카오맵/네이버지도/전화 연결·오프라인 폴백 내장)
- `scripts/`:
  - `update_prices.py`: 오피넷 API로 `docs/data/stations.json` 자동 갱신 (유종별 최소 반경 좌표 5~7회만 호출)
  - `sync_android_assets.py`: `docs/` 내용을 Android `assets/www/` 로 동기화
  - `generate_icons.py`: PWA 및 Android mipmap 아이콘 생성
- `.github/workflows/`:
  - `deploy-pages.yml`: GitHub Pages 무료 HTTPS 자동 배포 (PWA)
  - `update-prices.yml`: 하루 8회(KST 06:15~21:30) 자동 가격 갱신 및 Pages 재배포 (최대 208회/일)
  - `build-apk.yml`: Android `.apk` 클라우드 자동 빌드 및 GitHub Release 배포

---

## 배포 순서 (약 5분 소요, 무료)

### 1. GitHub 새 저장소 만들기 & 업로드
1. GitHub(`h17401792`)에서 새 저장소 생성: 추천 이름 **`daejeon-cashback-oil`** (Public 권장 — 무료 GitHub Pages 및 무제한 Public Actions 사용)
2. 이 폴더(`ontong_oil_mobile`)에서 PowerShell 열기:
   ```powershell
   git remote add origin https://github.com/h17401792/daejeon-cashback-oil.git
   git push -u origin main
   ```

### 2. 오피넷 API Key 비밀변수 등록 (중요: 코드에 노출 방지)
1. GitHub 저장소 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
2. Name: `OPINET_API_KEY`
3. Secret: 발급받은 본인의 오피넷 일반 API Key 입력 (`opinet_config.json` 참고)

### 3. GitHub Pages 활성화 (PWA URL 생성)
1. GitHub 저장소 → **Settings** → **Pages**
2. **Build and deployment → Source** 를 **`GitHub Actions`** 로 선택
3. **Actions** 탭에서 **`Deploy PWA to GitHub Pages`** 완료 후 접속 주소 확인:
   - `https://h17401792.github.io/daejeon-cashback-oil/`
   - 스마트폰 브라우저로 접속 → **앱 설치 / 홈 화면에 추가** 선택 시 바로 앱처럼 사용 가능!

### 4. Android APK 다운로드 & 배포
1. 푸시 후 **Actions** 탭의 **`Build Android APK`** 워크플로우가 완료되면 `daejeon-cashback-oil.apk` 가 자동 빌드됩니다.
2. 다운로드 위치:
   - 저장소 우측 **Releases** → `https://github.com/h17401792/daejeon-cashback-oil/releases/latest/download/daejeon-cashback-oil.apk`
   - 또는 **Actions** 실행 결과 하단 `Artifacts → daejeon-cashback-oil-apk`
3. 안드로이드 폰에 `.apk` 전달 후 설치 ("출처를 알 수 없는 앱 허용" 1회 승인)

---

## 주의 및 출처 안내
- 유가 정보 출처: 한국석유공사 오피넷(Opinet) Open API
- 캐시백 제공 여부는 대전 온통대전 앱 가맹점 목록 스냅샷 기준입니다.
- 본 프로젝트는 비공식 안내 앱이며, 캐시백 정책·예산 소진·휴폐업 여부는 결제 전 공식 앱에서 다시 확인해 주세요.
