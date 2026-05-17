import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useToast } from "@/hooks/use-toast";

interface MapProps {
  className?: string;
  location?: string;
  longitude?: number | null;
  latitude?: number | null;
  isSelectable?: boolean;
  onLocationSelect?: (lat: number, lng: number) => void;
}

const Map: React.FC<MapProps> = ({ 
  className, 
  location, 
  longitude, 
  latitude, 
  isSelectable = false,
  onLocationSelect 
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null); 
  
  const { toast } = useToast();
  
  // Hyderabad coordinates from the Footer/Project context
  const DEFAULT_HYD_LAT = 17.375685;
  const DEFAULT_HYD_LNG = 78.474661;
  const initialLng = longitude ?? DEFAULT_HYD_LNG;
  const initialLat = latitude ?? DEFAULT_HYD_LAT;

  useEffect(() => {
    if (!mapContainer.current) return;

    if (map.current) {
        map.current.remove();
        map.current = null;
    }
    
    // Fallback content if map initialization is not required or fails
    const fallbackContent = `
        <div class="flex items-center justify-center h-full bg-muted/20 rounded-lg border-2 border-dashed border-border">
            <div class="text-center p-4">
            <div class="text-lg font-medium text-foreground mb-2">📍 ${location || 'Location not specified'}</div>
            <div class="text-sm text-muted-foreground">Coordinates are unavailable for mapping.</div>
            </div>
        </div>
    `;

    // Only render the fallback if map is not selectable AND coordinates are entirely missing
    if (!isSelectable && (longitude === null || latitude === null)) {
        if (mapContainer.current) {
            mapContainer.current.innerHTML = fallbackContent;
        }
        return;
    }


    try {
      // NOTE: Using the key from your config.py/env file
      const LOCATIONIQ_API_KEY = "pk.edd24481c4b9e71cfe516546e880c14b"; 

      map.current = new maplibregl.Map({
        container: mapContainer.current,
        style: `https://tiles.locationiq.com/v3/streets/vector.json?key=${LOCATIONIQ_API_KEY}`,
        center: [initialLng, initialLat],
        zoom: (longitude && latitude) || isSelectable ? 12 : 10,
      });

      map.current.addControl(new maplibregl.NavigationControl(), 'top-right');
      
      const marker = new maplibregl.Marker({
        color: isSelectable ? '#DC2626' : '#0EA5E9', // Red for interactive (lost item), Blue otherwise
        draggable: isSelectable,
      })
        .setLngLat([initialLng, initialLat])
        .addTo(map.current);

      markerRef.current = marker;

      // Add Draggable/Click Logic (for isSelectable mode)
      if (isSelectable && onLocationSelect) {
        
        // 1. Drag End
        marker.on('dragend', () => {
          const lngLat = marker.getLngLat();
          onLocationSelect(lngLat.lat, lngLat.lng);
        });
        
        // 2. Map Click
        map.current.on('click', (e) => {
          marker.setLngLat(e.lngLat);
          onLocationSelect(e.lngLat.lat, e.lngLat.lng);
        });
      }

    } catch (error) {
      console.error('Map initialization error:', error);
      toast({
        title: "Map Error",
        description: "Could not load the map. Please try refreshing.",
        variant: "destructive",
      });
      // Display fallback content on map failure
      if (mapContainer.current) {
        mapContainer.current.innerHTML = fallbackContent;
      }
    }

    return () => {
      map.current?.remove();
    };
  }, [location, longitude, latitude, toast, isSelectable, onLocationSelect]); // onLocationSelect is stable now

  return (
    <div className={`w-full h-64 rounded-lg overflow-hidden ${className || ''}`}>
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
};

export default Map;