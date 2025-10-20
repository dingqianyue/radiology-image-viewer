'use client';

import { useEffect, useRef } from 'react';
import { Niivue } from '@niivue/niivue';

interface NiftiViewerProps {
    fileUrl: string;
}

export default function NiftiViewer({ fileUrl }: NiftiViewerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const nvRef = useRef<Niivue | null>(null);

    useEffect(() => {
        let nv: Niivue | null = null; // Declare nv here to be accessible in cleanup

        if (canvasRef.current) {
            nv = new Niivue({
                backColor: [0, 0, 0, 1],
                show3Dcrosshair: true,
            });

            nvRef.current = nv;
            nv.attachToCanvas(canvasRef.current);

            const volumeList = [
                {
                    url: fileUrl,
                    colormap: 'gray',
                    opacity: 1.0,
                }
            ];

            const loadVolume = async () => {
                try {
                    await nv?.loadVolumes(volumeList);
                } catch (error) {
                    console.error('Error loading NIfTI file:', error);
                }
            };
            loadVolume();
        }

        // Cleanup function
        return () => {
            if (nvRef.current && typeof nvRef.current.destroy === 'function') {
                try {
                    nvRef.current.destroy();
                    nvRef.current = null;
                    console.log("Niivue instance destroyed");
                } catch (error) {
                    console.error("Error destroying Niivue instance:", error);
                }
            } else {
                console.log("Niivue instance or destroy method not found for cleanup");
            }
        };
    }, [fileUrl]);

    return (
        <div className="w-full">
            <canvas
                ref={canvasRef}
                className="border rounded w-full h-[600px]" // Set a fixed height
            />
            <div className="mt-2 text-sm text-gray-600">
                <p>Tip: Click and drag to navigate through slices</p>
            </div>
        </div>
    );
}
