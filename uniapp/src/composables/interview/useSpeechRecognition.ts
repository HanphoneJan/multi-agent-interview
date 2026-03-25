/**
 * 语音识别 Composable
 * 支持 Web Speech API (浏览器) 和 uni-app 录音 + 第三方 ASR
 */

import { ref } from 'vue';

export type RecognitionStatus = 'idle' | 'listening' | 'processing' | 'error';

export interface UseSpeechRecognitionOptions {
  lang?: string;  // 语言，默认 'zh-CN'
  continuous?: boolean;  // 是否连续识别
  interimResults?: boolean;  // 是否返回中间结果
  onResult?: (text: string, isFinal: boolean) => void;
  onError?: (error: string) => void;
}

/**
 * 检查是否支持 Web Speech API
 */
const isWebSpeechSupported = (): boolean => {
  return 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
};

/**
 * 获取 SpeechRecognition 构造函数
 */
const getSpeechRecognition = (): any => {
  return (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
};

export function useSpeechRecognition(options: UseSpeechRecognitionOptions = {}) {
  const status = ref<RecognitionStatus>('idle');
  const transcript = ref('');
  const error = ref('');
  let recognition: any = null;

  const {
    lang = 'zh-CN',
    continuous = false,
    interimResults = true,
    onResult,
    onError
  } = options;

  /**
   * 开始语音识别 (Web Speech API)
   */
  const startListening = (): boolean => {
    // #ifdef H5
    if (!isWebSpeechSupported()) {
      error.value = '浏览器不支持语音识别';
      onError?.('浏览器不支持语音识别');
      return false;
    }

    try {
      const SpeechRecognition = getSpeechRecognition();
      recognition = new SpeechRecognition();

      recognition.lang = lang;
      recognition.continuous = continuous;
      recognition.interimResults = interimResults;

      recognition.onstart = () => {
        status.value = 'listening';
        error.value = '';
        transcript.value = '';
      };

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalTranscript += result[0].transcript;
          } else {
            interimTranscript += result[0].transcript;
          }
        }

        // 更新当前识别文本
        transcript.value = finalTranscript || interimTranscript;

        // 回调
        onResult?.(transcript.value, !!finalTranscript);
      };

      recognition.onerror = (event: any) => {
        status.value = 'error';
        error.value = event.error;
        onError?.(event.error);
      };

      recognition.onend = () => {
        status.value = 'idle';
        recognition = null;
      };

      recognition.start();
      return true;

    } catch (err) {
      status.value = 'error';
      error.value = String(err);
      onError?.(String(err));
      return false;
    }
    // #endif

    // #ifndef H5
    // 非 H5 环境不支持 Web Speech API
    error.value = '当前环境不支持语音识别，请使用文字输入';
    onError?.('当前环境不支持语音识别，请使用文字输入');
    return false;
    // #endif
  };

  /**
   * 停止语音识别
   */
  const stopListening = (): void => {
    // #ifdef H5
    if (recognition) {
      recognition.stop();
    }
    // #endif
    status.value = 'idle';
  };

  /**
   * 中止语音识别
   */
  const abortListening = (): void => {
    // #ifdef H5
    if (recognition) {
      recognition.abort();
    }
    // #endif
    status.value = 'idle';
  };

  return {
    status,
    transcript,
    error,
    isSupported: isWebSpeechSupported(),
    startListening,
    stopListening,
    abortListening
  };
}
