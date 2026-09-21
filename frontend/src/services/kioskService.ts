import { apiClient } from './apiClient';
import { FaceVerificationResponse, ManualPunchRequest, KioskStatsResponse } from '../types/api';

export const kioskService = {
  /**
   * Send a captured frame to the backend for face recognition and attendance punch.
   * @param imageBlob  JPEG blob from the live camera capture
   * @param scannerType  'CHECK_IN' | 'CHECK_OUT'
   */
  async verifyFaceAndPunch(
    imageBlob: Blob,
    scannerType: 'CHECK_IN' | 'CHECK_OUT' = 'CHECK_IN'
  ): Promise<FaceVerificationResponse> {
    const formData = new FormData();
    formData.append('image', imageBlob, 'kiosk_frame.jpg');
    formData.append('scanner_type', scannerType);
    return apiClient.postMultipart<FaceVerificationResponse>(
      `/attendance/verify-face?scanner_type=${scannerType}`,
      formData,
      20000 // 20 s for inference
    );
  },

  /**
   * Manual punch by employee ID (operator override).
   */
  async manualPunch(request: ManualPunchRequest): Promise<FaceVerificationResponse> {
    return apiClient.post<FaceVerificationResponse>('/attendance/manual-punch', request);
  },

  /**
   * Today's kiosk gate statistics.
   */
  async getKioskStats(): Promise<KioskStatsResponse> {
    return apiClient.get<KioskStatsResponse>('/attendance/kiosk-stats');
  },
};
