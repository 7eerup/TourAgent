'use client';
import React, { useRef, useEffect, useState } from 'react';                   // React 훅 사용을 위해 가져옵니다.
import { usePlaceDescription } from '@/hooks/map/PlaceDescription';            // 장소 상세 정보를 캐싱하는 커스텀 훅
import { makeInfoWindowContent } from './InfoWindowContent';                        // InfoWindow에 렌더링할 HTML 생성 함수

/**
 * MapSection 컴포넌트
 * - 네이버 지도를 초기화하고
 * - 주어진 장소에 따라 마커를 표시하며
 * - 마우스 호버 시 상세 정보를 보여줍니다.
 * @param {{ places: Array }} props
 */
export default function MapSection({ places }) {
  const mapRef = useRef(null);                // 지도 DOM을 참조할 ref
  const [map, setMap] = useState(null);       // 네이버 지도 인스턴스를 저장할 state
  const [infoWindow, setInfoWindow] = useState(null); // InfoWindow 인스턴스를 저장할 state
  const markersRef = useRef([]);               // 생성된 마커들을 추적하기 위한 ref

  // 장소별 상세정보(로컬 + 이미지)를 캐싱하는 훅 호출
  const { detailsMap, loadingMap } = usePlaceDescription(places);

  // 지도 초기화: 컴포넌트 마운트 시 한 번 실행
  useEffect(() => {
    // mapRef가 준비되고, 아직 map이 없을 때만 초기화
    if (!mapRef.current || map) return;

    //   // 처음 한 번 투명 처리
    // mapRef.current.firstElementChild.style.background = 'transparent';

    // // 줌·타일이 바뀔 때마다 재적용
    // window.naver.maps.Event.addListener(map, 'tilesloaded', () => {
    //     mapRef.current.firstElementChild.style.background = 'transparent';
    // });

    // 초기 중심 좌표 설정 (서울광장 부근)
    const center = new window.naver.maps.LatLng(37.5665, 126.9780);
    // 지도 옵션
    const mapOptions = {
      center,                                 // 지도 중심
      zoom: 15,                               // 초기 줌 레벨
      minZoom: 6,                             // 최소 줌 레벨
      zoomControl: false,                     // 줌 컨트롤 비활성화
      scaleControl: false,                    // 스케일 컨트롤 비활성화
      logoControl: true,                      // 로고 표시
      mapDataControl: true,                   // 데이터 컨트롤 표시
    };
    // 지도 인스턴스 생성
    const naverMap = new window.naver.maps.Map(mapRef.current, mapOptions);
    setMap(naverMap);                         // 상태에 저장

    // InfoWindow 인스턴스 생성 (닫기 버튼 포함)
    const iw = new window.naver.maps.InfoWindow({ removable: true });
    setInfoWindow(iw);                        // 상태에 저장
  }, [mapRef, map]);                          // mapRef, map 의존성

  // 2) 배경 투명 처리: 맵이 준비되면 한 번 적용하고, 타일 로드 때마다 재적용
  useEffect(() => {
    if (!map) return;
    const container = mapRef.current;
    const makeTransparent = () => {
      // map-canvas > 첫 번째 div
      const firstDiv = container.querySelector('.map-canvas > div');
      if (firstDiv) firstDiv.style.background = 'transparent';
    };

    // 초기 한 번
    makeTransparent();
    // 타일이 바뀔 때마다
    const listener = window.naver.maps.Event.addListener(map, 'tilesloaded', makeTransparent);

    return () => {
      window.naver.maps.Event.removeListener(listener);
    };
  }, [map]);

  // 3) 마커 렌더링 (생략)
  useEffect(() => {
    if (!map || !infoWindow) return;
    markersRef.current.forEach(m => m.setMap(null));
    markersRef.current = [];

    const bounds = new window.naver.maps.LatLngBounds();
    places.forEach(place => {
      const pos = new window.naver.maps.LatLng(place.map_x, place.map_y);
      const marker = new window.naver.maps.Marker({ position: pos, map, title: place.name, animation: window.naver.maps.Animation.BOUNCE });
      setTimeout(() => marker.setAnimation(null), 700);
      window.naver.maps.Event.addListener(marker, 'mouseover', () => {
        if (loadingMap[place.name] || !detailsMap[place.name]) {
          infoWindow.setContent('<div style="padding:10px;">로딩 중…</div>');
        } else {
          const { local, images } = detailsMap[place.name];
          infoWindow.setContent(makeInfoWindowContent(local.items?.[0] || {}, images));
        }
        infoWindow.open(map, marker);
      });
      window.naver.maps.Event.addListener(marker, 'mouseout', () => infoWindow.close());
      markersRef.current.push(marker);
      bounds.extend(pos);
    });
    map.panToBounds(bounds, { duration: 1000 }, 100);
  }, [places, map, infoWindow, detailsMap, loadingMap]);

  const zoomIn = () => map.setZoom(map.getZoom() + 1, true);
  const zoomOut = () => map.setZoom(map.getZoom() - 1, true);

  // JSX 반환: 지도 컨테이너 및 줌 버튼
  return (
    // <div className="w-1/2 bg-gray-200 relative">
    //   {/* 지도 DOM */}
    //   <div ref={mapRef} className="w-full h-full" />
    //   {/* 줌 버튼 */}
    //   <div className="absolute bottom-5 right-5 flex flex-col space-y-px">
    //     <button onClick={zoomIn} className="w-10 h-10 flex items-center justify-center bg-white/[.90] backdrop-blur-sm rounded-t-lg text-gray-700 hover:bg-white text-xl shadow-md">+</button>
    //     <button onClick={zoomOut} className="w-10 h-10 flex items-center justify-center bg-white/[.90] backdrop-blur-sm rounded-b-lg text-gray-700 hover:bg-white text-xl shadow-md">-</button>
    //   </div>
    // </div>
    <div className="w-1/2 h-full relative">
      {/* 지도 DOM */}
      <div ref={mapRef} className="w-full h-full map-canvas" />
      {/* 줌 버튼 */}
      <div className="absolute bottom-5 right-5 flex flex-col space-y-px">
        <button onClick={zoomIn} className="w-10 h-10 flex items-center justify-center bg-white/[.90] backdrop-blur-sm rounded-t-lg text-gray-700 hover:bg-white text-xl shadow-md">+</button>
        <button onClick={zoomOut} className="w-10 h-10 flex items-center justify-center bg-white/[.90] backdrop-blur-sm rounded-b-lg text-gray-700 hover:bg-white text-xl shadow-md">-</button>
          {/* styled-jsx 글로벌 선언 */}
      <style jsx global>{`
        /* 네이버맵의 첫 번째 child DIV 배경을 무조건 투명으로 덮어씌웁니다 */
        .map-canvas > div {
          background: transparent !important;
        }
      `}</style>
      </div>
    </div>
  );
}
