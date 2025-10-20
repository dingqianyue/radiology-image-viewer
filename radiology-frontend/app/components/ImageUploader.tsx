'use client';

import { useState } from 'react';
import axios from 'axios';

interface ImageUploaderProps {
    userId: string;
    onJobCreated: (jobId: string) => void;
}

// Define the available task types
type TaskType = "blur" | "resize" | "grayscale";

export default function ImageUploader({ userId, onJobCreated }: ImageUploaderProps) {
    const [files, setFiles] = useState<FileList | null>(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string>('');
    const [taskType, setTaskType] = useState<TaskType>('blur');

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFiles(e.target.files);
        setError('');
    };

    const handleUpload = async () => {
        if (!files || files.length === 0) {
            setError('Please select at least one file');
            return;
        }

        setUploading(true);
        setError('');

        try {
            const formData = new FormData();

            // Add all files to form data
            Array.from(files).forEach((file) => {
                formData.append('files', file);
            });

            // Add the selected task type to the form data
            formData.append('task_type', taskType);

            // Upload to backend
            const response = await axios.post(
                'http://localhost:8000/jobs',
                formData,
                {
                    headers: {
                        'X-User-ID': userId,
                    },
                }
            );

            // Notify parent component
            onJobCreated(response.data.job_id);

            // Clear file input
            setFiles(null);
            const fileInput = document.getElementById('file-input') as HTMLInputElement;
            if (fileInput) fileInput.value = '';

        } catch (err: any) {
            console.error('Upload error:', err);
            setError(err.response?.data?.detail || 'Upload failed. Please try again.');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Upload Images</h2>

            <div className="space-y-4">
                {/* File input */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Select images to process
                    </label>
                    <input
                        id="file-input"
                        type="file"
                        multiple
                        accept=".png,.jpg,.jpeg,.dcm,.nii,.nii.gz,.gz"
                        onChange={handleFileChange}
                        className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-50 file:text-blue-700
              hover:file:bg-blue-100
              cursor-pointer"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                        Supported: PNG, JPG, DICOM (.dcm), NIfTI (.nii, .nii.gz)
                    </p>
                </div>

                {/* Task Type Selector */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Select processing task
                    </label>
                    <select
                        value={taskType}
                        onChange={(e) => setTaskType(e.target.value as TaskType)}
                        className="block w-full border-gray-300 rounded-md shadow-sm
                                   focus:ring-blue-500 focus:border-blue-500
                                   py-2 px-3 bg-white"
                    >
                        <option value="blur">Gaussian Blur</option>
                        <option value="resize">Resize (512x512)</option>
                        <option value="grayscale">Grayscale</option>
                    </select>
                </div>

                {/* Selected files preview */}
                {files && files.length > 0 && (
                    <div className="bg-gray-50 p-3 rounded">
                        <p className="text-sm font-medium text-gray-700 mb-2">
                            Selected files ({files.length}):
                        </p>
                        <ul className="text-sm text-gray-600 space-y-1">
                            {Array.from(files).map((file, index) => (
                                <li key={index} className="truncate">
                                    {file.name} ({(file.size / 1024).toFixed(1)} KB)
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Upload button */}
                <button
                    onClick={handleUpload}
                    disabled={!files || uploading}
                    className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg
            font-medium hover:bg-blue-700 disabled:bg-gray-300
            disabled:cursor-not-allowed transition-colors"
                >
                    {uploading ? 'Uploading...' : 'Upload & Process'}
                </button>

                {/* Error message */}
                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                        {error}
                    </div>
                )}
            </div>
        </div>
    );
}
