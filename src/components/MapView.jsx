import React, { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import { IGN_WMTS_URL, MAP_CENTER, MAP_ZOOM, PALETTES } from '../config.js'

/**
 * Carte Leaflet : fond IGN et choroplèthe communal.
 *
 * Le fond de plan est le Plan IGN, clair, sur un chrome sombre : c'est lui
 * qui doit ressortir. Aucune animation, aucun dégradé — la lisibilité d'un
 * jeu de planches se joue sur la constance de la sémiologie.
 */
export default function MapView({ territoire, champ, palette, format, onSurvol }) {
  const refDiv = useRef(null)
  const refCarte = useRef(null)
  const refCouche = useRef(null)
  const [bornes, setBornes] = useState(null)

  // ── Création de la carte, une seule fois ──────────────────────────────────
  useEffect(() => {
    if (refCarte.current || !refDiv.current) return

    const carte = L.map(refDiv.current, {
      center: MAP_CENTER,
      zoom: MAP_ZOOM,
      zoomControl: true,
      attributionControl: true,
    })

    // Service de tuiles de la Géoplateforme : Leaflet substitue {z}/{x}/{y}
    // nativement. La substitution d'emprise relève d'une autre bibliothèque.
    L.tileLayer(IGN_WMTS_URL, {
      attribution: 'Fonds de plan : IGN — Géoplateforme',
      maxZoom: 18,
      minZoom: 6,
      opacity: 0.85,
    }).addTo(carte)

    refCarte.current = carte
    return () => {
      carte.remove()
      refCarte.current = null
    }
  }, [])

  // ── Couche choroplèthe, redessinée à chaque changement d'indicateur ───────
  useEffect(() => {
    const carte = refCarte.current
    if (!carte || !territoire) return

    if (refCouche.current) {
      carte.removeLayer(refCouche.current)
      refCouche.current = null
    }

    const valeurs = territoire.features
      .map((f) => f.properties[champ])
      .filter((v) => typeof v === 'number' && Number.isFinite(v))
    const min = Math.min(...valeurs)
    const max = Math.max(...valeurs)
    const couleurs = PALETTES[palette]

    function couleurDe(v) {
      if (typeof v !== 'number' || !Number.isFinite(v)) return '#2a2a4a'
      if (max === min) return couleurs[couleurs.length - 1]
      const t = (v - min) / (max - min)
      return couleurs[Math.min(couleurs.length - 1, Math.floor(t * couleurs.length))]
    }

    const couche = L.geoJSON(territoire, {
      style: (f) => ({
        fillColor: couleurDe(f.properties[champ]),
        fillOpacity: 0.72,
        color: '#0b1224',
        weight: 1,
      }),
      onEachFeature: (f, lc) => {
        lc.bindTooltip(
          `<strong>${f.properties.nom}</strong><br>${format(f.properties[champ])}`,
          { sticky: true, className: 'survol' }
        )
        lc.on('mouseover', () => {
          lc.setStyle({ weight: 2.5, color: '#5CA6E0' })
          onSurvol?.(f.properties)
        })
        lc.on('mouseout', () => {
          lc.setStyle({ weight: 1, color: '#0b1224' })
          onSurvol?.(null)
        })
      },
    }).addTo(carte)

    refCouche.current = couche
    setBornes({ min, max, couleurs })

    // Leaflet mesure son conteneur a la creation : si les donnees arrivent
    // apres, le cadrage est calcule sur une taille perimee. On redimensionne
    // avant d'ajuster l'emprise, et une seconde fois au cas ou la mise en page
    // se stabilise apres la premiere image.
    const ajuster = () => {
      carte.invalidateSize(false)
      carte.fitBounds(couche.getBounds(), { padding: [24, 24] })
    }
    ajuster()
    const t = setTimeout(ajuster, 400)
    window.addEventListener('resize', ajuster)
    return () => {
      clearTimeout(t)
      window.removeEventListener('resize', ajuster)
    }
  }, [territoire, champ, palette, format, onSurvol])

  return (
    <>
      <div ref={refDiv} className="leaflet-hote" />
      {bornes && (
        <div className="legende" data-ob-anchor="legende">
          <div className="legende-titre">Échelle</div>
          <div className="legende-bandes">
            {bornes.couleurs.map((c, i) => (
              <span key={i} style={{ background: c }} />
            ))}
          </div>
          <div className="legende-bornes">
            <span>{format(bornes.min)}</span>
            <span>{format(bornes.max)}</span>
          </div>
          <div className="legende-classes">
            {bornes.couleurs.length} classes, bornes égales
          </div>
        </div>
      )}
    </>
  )
}
