'use client';

import { useEffect, useRef } from 'react';
import { Niivue, NVImage } from '@niivue/niivue';

interface NiftiViewerProps {
    fileUrl: string;
}

export default function NiftiViewer({ fileUrl }: NiftiViewerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const nvRef = useRef<Niivue | null>(null);

    useEffect(() => {
        if (!canvasRef.current) return;

        // Initialize Niivue
        const nv = new Niivue({
            backColor: [0, 0, 0, 1],
            show3Dcrosshair: true,
            onLocationChange: (data) => {
                console.log('Location changed:', data);
            }
        });

        nvRef.current = nv;
        nv.attachToCanvas(canvasRef.current);

        // Load the NIfTI volume
        const volumeList = [
            {
                url: fileUrl,
                colormap: 'gray',
                opacity: 1.0,
            }
        ];

        nv.loadVolumes(volumeList).catch((error) => {
            console.error('Error loading NIfTI file:', error);
        });

        // Cleanup
        return () => {
            if (nvRef.current) {
                nvRef.current.detachFromCanvas();
                nvRef.current = null;
            }
        };
    }, [fileUrl]);

    return (
        <div className="w-full">
            <canvas
                ref={canvasRef}
                width={600}
                height={600}
                className="border rounded max-w-full"
            />
            <div className="mt-2 text-sm text-gray-600">
                <p>💡 Tip: Click and drag to navigate through slices</p>
            </div>
        </div>
    );
}
