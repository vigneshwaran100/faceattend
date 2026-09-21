import { apiClient } from './apiClient';
import { FaceSamplesEnrollmentResponse, FaceEnrollmentResponse } from '../types/api';

/**
 * Converts a base64 DataURL string to a File/Blob object
 */
export function dataURLtoFile(dataUrl: string, filename: string): File {
  const arr = dataUrl.split(',');
  const mimeMatch = arr[0].match(/:(.*?);/);
  const mime = mimeMatch ? mimeMatch[1] : 'image/jpeg';
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new File([u8arr], filename, { type: mime });
}

export const faceEnrollmentService = {
  /**
   * Enrolls exactly 10 multi-pose face samples for an employee
   * Required sequence: Front x2, Left x2, Right x2, Up x2, Down x2
   */
  async enrollFaceSamples(
    employeeId: string,
    sampleDataUrls: string[]
  ): Promise<FaceSamplesEnrollmentResponse> {
    if (sampleDataUrls.length !== 10) {
      throw new Error(`Exactly 10 face sample images are required, received ${sampleDataUrls.length}`);
    }

    const formData = new FormData();
    sampleDataUrls.forEach((dataUrl, idx) => {
      const file = dataURLtoFile(dataUrl, `sample_${idx + 1}.jpg`);
      formData.append('images', file);
    });

    return apiClient.postMultipart<FaceSamplesEnrollmentResponse>(
      `/employees/${employeeId}/face/samples`,
      formData,
      45000 // 45 second timeout for multi-image vector embedding generation
    );
  },

  /**
   * Single image fallback enrollment
   */
  async enrollSingleImage(
    employeeId: string,
    imageFile: File | Blob
  ): Promise<FaceEnrollmentResponse> {
    const formData = new FormData();
    formData.append('image', imageFile, 'face_capture.jpg');

    return apiClient.postMultipart<FaceEnrollmentResponse>(
      `/employees/${employeeId}/face`,
      formData,
      30000
    );
  },
};
