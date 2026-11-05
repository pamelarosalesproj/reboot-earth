import L from 'leaflet'
import { useEffect } from 'react'
import { GeoJSON, MapContainer, TileLayer, useMap } from 'react-leaflet'
import { t } from '../i18n/pt-BR'

function FitBounds({ geometry }: { geometry: GeoJSON.Geometry }) {
  const map = useMap()
  useEffect(() => {
    const bounds = L.geoJSON(geometry).getBounds()
    if (bounds.isValid()) map.fitBounds(bounds, { padding: [16, 16] })
  }, [geometry, map])
  return null
}

export default function CarMap({ geometry, height = 200 }: { geometry: GeoJSON.Geometry | null; height?: number }) {
  if (!geometry) {
    return (
      <div className="map-empty" style={{ height }}>
        {t.panel.noPolygon}
      </div>
    )
  }
  return (
    <MapContainer className="car-map" style={{ height }} center={[-14, -51]} zoom={4} scrollWheelZoom={false}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <GeoJSON data={geometry} style={{ color: '#2f6b3a', weight: 2, fillOpacity: 0.25 }} />
      <FitBounds geometry={geometry} />
    </MapContainer>
  )
}
