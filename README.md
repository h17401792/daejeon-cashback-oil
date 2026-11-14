# 대전 캐시백 주유 지도 (PWA + Android APK)

대전 지역화폐 **온통대전(대전사랑카드)** 캐시백 제공 주유소·LPG충전소 **82곳**의 유가와 캐시백 체감가를 비교하는 모바일 앱입니다.

## 배포 주소 (개인 ID 미노출 Netlify 구성)
- **PWA 웹앱 (안드로이드·아이폰 공용):** https://daejeon-oil.netlify.app/
- **Android APK 다운로드:** https://daejeon-oil.netlify.app/download/daejeon-cashback-oil.apk

## 구조
- `docs/`: 설치형 웹앱(PWA) 정적 파일 (`index.html`, `manifest.webmanifest`, `sw.js`, `data/stations.json`, `icons/`, `_headers`)
- `android/`: Android APK 네이티브 WebView 래퍼 프로젝트 (위치 권한·카카오맵/네이버지도/전화 연결·오프라인 폴백 내장)
- `scripts/`:
  - `update_prices.py`: 오피넷 API로 `docs/data/stations.json` 자동 갱신 (유종별 최소 반경 좌표 5~7회만 호출)
  - `sync_android_assets.py`: `docs/` 내용을 Android `assets/www/` 로 동기화
  - `generate_icons.py`: PWA 및 Android mipmap 아이콘 생성
- `.github/workflows/`:
  - `deploy-netlify.yml`: `docs/` 와 최신 APK를 Netlify (`daejeon-oil`) 로 자동 배포
  - `update-prices.yml`: 하루 8회(KST 06:15~21:30) 자동 가격 갱신 및 Netlify 재배포 (최대 208회/일)
  - `build-apk.yml`: Android `.apk` 클라우드 자동 빌드 후 Netlify `/download/daejeon-cashback-oil.apk` 로 게시

---

## 비공개(Private) 전환 및 Netlify 자동 배포 마무리
1. GitHub 저장소 **Settings → Danger Zone → Change visibility → Private** 으로 변경 (외부에 아이디/코드/페이지 완전 비공개)
2. Netlify Access Token 발급: https://app.netlify.com/user/applications#personal-access-tokens → **New access token**
3. GitHub 저장소 **Settings → Secrets and variables → Actions → New repository secret** 등록:
   - `OPINET_API_KEY`: 오피넷 일반 Key
   - `NETLIFY_AUTH_TOKEN`: 위 Netlify Personal access token
4. **Actions → Build Android APK & Publish to Netlify → Run workflow** 1회 실행
