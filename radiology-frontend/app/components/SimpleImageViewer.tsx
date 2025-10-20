'use client';

interface SimpleImageViewerProps {
    src: string;
}

export default function SimpleImageViewer({ src }: SimpleImageViewerProps) {
    return (
        <div className="w-full">
            <img
                src={src}
                alt="Medical image"
                className="max-w-full h-auto rounded border"
                onError={(e) => {
                    console.error('Image load error:', src);
                    e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ddd" width="200" height="200"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3EImage Load Error%3C/text%3E%3C/svg%3E';
                }}
            />
        </div>
    );
}
