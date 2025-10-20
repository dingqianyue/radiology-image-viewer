'use client';

import { useState } from 'react';
import ImageUploader from './components/ImageUploader';
import JobStatus from './components/JobStatus';
import SimpleImageViewer from './components/SimpleImageViewer';
import NiftiViewer from './components/NiftiViewer';

export default function Home() {
    const [currentJobId, setCurrentJobId] = useState<string>('');
    const [userId, setUserId] = useState<string>('user123'); // Simulate user ID
    const [processedImages, setProcessedImages] = useState<string[]>([]);

    return (
        <main className="min-h-screen p-8 bg-gray-50">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">
                        Radiology Image Viewer
                    </h1>
                    <p className="text-gray-600">
                        Upload and process medical images (PNG, JPG, DICOM, NIfTI)
                    </p>
                </div>

                {/* User ID Selector (for testing multi-user isolation) */}
                <div className="mb-6 bg-white p-4 rounded-lg shadow">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        User ID (for testing isolation):
                    </label>
                    <input
                        type="text"
                        value={userId}
                        onChange={(e) => setUserId(e.target.value)}
                        className="border rounded px-3 py-2 w-64"
                        placeholder="Enter user ID"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                        Change this to test multi-user isolation
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Left Column - Upload & Status */}
                    <div className="space-y-6">
                        <ImageUploader
                            userId={userId}
                            onJobCreated={setCurrentJobId}
                        />

                        {currentJobId && (
                            <JobStatus
                                jobId={currentJobId}
                                userId={userId}
                                onComplete={(images) => setProcessedImages(images)}
                            />
                        )}
                    </div>

                    {/* Right Column - Image Viewers */}
                    <div className="space-y-6">
                        <div className="bg-white p-6 rounded-lg shadow">
                            <h2 className="text-xl font-semibold mb-4">Processed Images</h2>

                            {processedImages.length === 0 ? (
                                <div className="text-center py-12 text-gray-400">
                                    <p>No processed images yet</p>
                                    <p className="text-sm">Upload images to get started</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {processedImages.map((imagePath, index) => (
                                        <div key={index} className="border rounded p-4">
                                            <p className="text-sm text-gray-600 mb-2">
                                                Image {index + 1}
                                            </p>
                                            {imagePath.endsWith('.nii') || imagePath.endsWith('.nii.gz') ? (
                                                <NiftiViewer fileUrl={imagePath} />
                                            ) : (
                                                <SimpleImageViewer src={imagePath} />
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
