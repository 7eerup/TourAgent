import React from 'react';

// item: 네이버 Local Search API의 첫 번째 결과 객체
// images: 네이버 Image Search API의 items 배열
export function makeInfoWindowContent(item, images) {
  // 제목에서 <b> 태그를 제거하여 순수 텍스트로 변환합니다.
  const titleText = (item.title || '').replace(/<[^>]+>/g, '');
  
  // 주소 정보 (도로명 또는 지번) 또는 기본값 설정
  const roadAddress = item.roadAddress || '정보 없음';
  const jibunAddress = item.address || '정보 없음';
  
  // 전화번호 또는 기본값 설정
  const telephone = item.telephone || '정보 없음';
  
  // 카테고리 또는 기본값 설정
  const category = item.category || '정보 없음';
  
  // 설명(detail) 또는 기본값 설정
  const description = item.description || '설명 없음';
  
  // 4) 모든 images 항목에 대해 숫자형 width/height 속성 추가
  const parsedImages = images.map(img => {
    // 4-1) parseInt로 정수 변환, 실패(NaN)이면 0 할당
    const numericWidth  = parseInt(img.sizewidth,  10) || 0;
    const numericHeight = parseInt(img.sizeheight, 10) || 0;
    // 4-2) 기존 img 객체에 numericWidth/Height 필드를 붙여서 반환
    return { ...img, numericWidth, numericHeight };
  });

  // 5) 숫자로 변환된 width·height가 둘 다 양수인 항목만 필터링
  const validSizeImages = parsedImages.filter(img =>
    img.numericWidth  > 0 &&
    img.numericHeight > 0
  );

  // 6) 해상도(numericWidth * numericHeight) 내림차순 정렬
  const sortedByResolution = validSizeImages.sort((a, b) => {
    return (b.numericWidth * b.numericHeight)
         - (a.numericWidth * a.numericHeight);
  });

  // 7) 정렬된 배열의 첫 번째(최고 해상도) 객체를 bestImage로 선택
  const bestImage = sortedByResolution.length > 0
    ? sortedByResolution[0]
    : null;


  // 메인 이미지 (첫 번째 이미지) -> 최적화 이미지로 변경
  const mainImageHtml = bestImage ? `
    <div style="position:relative; width:100%; height:200px; border-radius:12px; overflow:hidden; margin-bottom:12px;">
      <img src="${bestImage.thumbnail}" alt="${(titleText || '').replace(/<[^>]+>/g, '')}" 
           style="width:100%; height:100%; object-fit:cover; border:none !important;" />
    </div>
  ` : '';
  
  // 평점 표시
  const ratingHtml = `
    <div style="display:flex; align-items:center; gap:4px; margin-bottom:4px;">
      <span style="color:#ffa500; font-size:14px;">★</span>
      <span style="font-weight:600; font-size:14px;">4.1</span>
      <span style="color:#666; font-size:12px;">(리뷰 수)</span>
    </div>
  `;
  
  // 전체 HTML 문자열을 반환합니다.
  return `
    <style>
      /* 네이버 지도 API 기본 스타일 강제 덮어쓰기 */
      .infoWindow,
      .infoWindow *,
      .custom-infowindow,
      .custom-infowindow *,
      .custom-infowindow *:before,
      .custom-infowindow *:after,
      div[style*="border"],
      div[style*="outline"] {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        -webkit-box-shadow: none !important;
        -moz-box-shadow: none !important;
        -webkit-border-radius: 0 !important;
        -moz-border-radius: 0 !important;
      }
      
      /* 네이버 지도 InfoWindow 컨테이너 스타일 재정의 */
      .infoWindow {
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        border-radius: 0 !important;
      }
      
      .custom-infowindow {
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        position: relative !important;
      }
      
      .custom-infowindow img {
        border: none !important;
        outline: none !important;
      }
      
      .custom-infowindow button {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
      }
      
      .custom-infowindow button:focus,
      .custom-infowindow button:active,
      .custom-infowindow button:hover {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
      }
      
      /* 네이버 지도 API가 추가하는 가능한 클래스들 */
      .marker_label,
      .marker_label *,
      .info_window,
      .info_window * {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
      }
    </style>
    <!-- 마커와 InfoWindow를 연결하는 투명 브릿지 (간격 줄임) -->
    <div style="position:absolute; bottom:-10px; left:50%; transform:translateX(-50%); width:40px; height:10px; background:transparent; z-index:1000;"></div>
    
    <div class="custom-infowindow" style="position:relative; max-width:320px; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:white; border-radius:16px; overflow:hidden; border:none !important; outline:none !important; box-shadow:0 4px 20px rgba(0,0,0,0.15) !important; padding:0 !important; margin:0 !important;">
      <!-- 하단 화살표 (꼬리) - 간격 줄임 -->
      <div style="position:absolute; bottom:-6px; left:50%; transform:translateX(-50%); width:0; height:0; border-left:8px solid transparent; border-right:8px solid transparent; border-top:6px solid white; z-index:999;"></div>
      
      ${mainImageHtml}
      <div style="padding:16px; border:none !important;">
        <h3 style="margin:0 0 4px; font-weight:700; font-size:18px; color:#333; border:none !important;">${titleText}</h3>
        ${ratingHtml}
        <div style="margin-bottom:8px; border:none !important;">
          <span style="color:#666; font-size:13px; margin-right:8px;">${category}</span>
          <span style="color:#666; font-size:13px;">•</span>
          <span style="color:#666; font-size:13px; margin-left:8px;">${roadAddress.split(' ').slice(0, 2).join(' ')}</span>
        </div>
        <p style="margin:0 0 12px; color:#666; font-size:13px; line-height:1.4; border:none !important;">
          ${description.length > 80 ? description.substring(0, 80) + '...' : description}
        </p>
        <div style="border-top:1px solid #eee; padding-top:12px; font-size:12px; color:#666; border-left:none !important; border-right:none !important; border-bottom:none !important;">
          <div style="margin-bottom:4px; border:none !important;"><strong>전화:</strong> ${telephone}</div>
          <div style="border:none !important;"><strong>주소:</strong> ${roadAddress}</div>
        </div>
      </div>
    </div>
  `;
}