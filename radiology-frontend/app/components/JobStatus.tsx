'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface JobStatusProps {
    jobId: string;
    userId: string;
    onComplete: (images: string[]) => void;
}

interface TaskResult {
    task_id: string;
    status: string;
    progress: number;
    result: any;
}

export default function JobStatus({ jobId, userId, onComplete }: JobStatusProps) {
    const [status, setStatus] = useState<string>('PENDING');
    const [progress, setProgress] = useState<number>(0);
    const [tasks, setTasks] = useState<TaskResult[]>([]);
    const [error, setError] = useState<string>('');

    useEffect(() => {
        // Poll for job status every 2 seconds
        const interval = setInterval(async () => {
            try {
                const response = await axios.get(
                    `http://localhost:8000/jobs/${jobId}`,
                    {
                        headers: {
                            'X-User-ID': userId,
                        },
                    }
                );

                setStatus(response.data.status);
                setProgress(response.data.progress);
                setTasks(response.data.task_results || []);

                // If job is complete, notify parent and stop polling
                if (response.data.status === 'SUCCESS') {
                    clearInterval(interval);

                    // Extract processed image URLs
                    const processedImages = response.data.task_results
                        .filter((task: TaskResult) => task.result?.output_file)
                        .map((task: TaskResult) => {
                            // Convert file path to URL
                            const filePath = task.result.output_file;
                            // Extract user_id, job_id, filename from path
                            const parts = filePath.split('/');
                            const filename = parts[parts.length - 1];
                            return `http://localhost:8000/files/${userId}/${jobId}/${filename}`;
                        });

                    onComplete(processedImages);
                } else if (response.data.status === 'FAILED') {
                    clearInterval(interval);
                    setError('Job failed. Please try again.');
                }
            } catch (err: any) {
                console.error('Status polling error:', err);
                if (err.response?.status === 404) {
                    setError('Job not found or access denied');
                    clearInterval(interval);
                }
            }
        }, 2000);

        // Cleanup
        return () => clearInterval(interval);
    }, [jobId, userId, onComplete]);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'SUCCESS':
                return 'bg-green-100 text-green-800 border-green-200';
            case 'FAILED':
                return 'bg-red-100 text-red-800 border-red-200';
            case 'RUNNING':
                return 'bg-blue-100 text-blue-800 border-blue-200';
            default:
                return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Processing Status</h2>

            <div className="space-y-4">
                {/* Job ID */}
                <div>
                    <p className="text-sm text-gray-600">Job ID:</p>
                    <p className="text-xs font-mono bg-gray-50 p-2 rounded break-all">
                        {jobId}
                    </p>
                </div>

                {/* Overall status */}
                <div>
                    <div className={`px-4 py-3 rounded border ${getStatusColor(status)}`}>
                        <p className="font-medium">Status: {status}</p>
                        <p className="text-sm">Overall Progress: {progress}%</p>
                    </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                    <div
                        className="bg-blue-600 h-4 transition-all duration-300 ease-out"
                        style={{ width: `${progress}%` }}
                    />
                </div>

                {/* Task details */}
                {tasks.length > 0 && (
                    <div>
                        <p className="text-sm font-medium text-gray-700 mb-2">
                            Tasks ({tasks.length}):
                        </p>
                        <div className="space-y-2">
                            {tasks.map((task, index) => (
                                <div
                                    key={task.task_id}
                                    className="bg-gray-50 p-3 rounded text-sm"
                                >
                                    <div className="flex justify-between items-center">
                                        <span className="font-medium">Task {index + 1}</span>
                                        <span className={`px-2 py-1 rounded text-xs ${task.status === 'SUCCESS' ? 'bg-green-100 text-green-800' :
                                            task.status === 'RUNNING' ? 'bg-blue-100 text-blue-800' :
                                                task.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                                                    'bg-gray-100 text-gray-800'
                                            }`}>
                                            {task.status}
                                        </span>
                                    </div>
                                    <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className="bg-blue-500 h-2 rounded-full transition-all"
                                            style={{ width: `${task.progress}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

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
