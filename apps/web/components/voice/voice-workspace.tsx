'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';

import { getOrganizations, refreshAccessToken } from '@/lib/chat-api';
import { createConversation, sendChatMessage } from '@/lib/chat-api';
import {
  createVoiceSession,
  decideVoiceConfirmation,
  getVoiceConsent,
  getVoiceSession,
  parseVoiceCommand,
  setVoiceConsent,
  uploadVoiceAudio,
} from '@/lib/voice-api';
import { VoiceBackground } from './voice-background';
import { SystemHeader } from './SystemHeader';
import { VoiceControls } from './VoiceControls';
import { TelemetryPanel } from './TelemetryPanel';
import { AetherCore } from './AetherCore';
import { ConversationTimeline, TimelineMessage } from './ConversationTimeline';
import { VoiceTerminal } from './voice-terminal';
import { DevDebugPanel } from './DevDebugPanel';

type PendingConfirmation = {
  confirmation_id: string;
  intent_type: string;
  transcript: string;
  payload?: any;
};

export function VoiceWorkspace() {
  const [captureEnabled, setCaptureEnabled] = useState(false);
  const [retentionEnabled, setRetentionEnabled] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [transcript, setTranscript] = useState('');
  const [pending, setPending] = useState<PendingConfirmation | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Real-time voice states
  const [isRecording, setIsRecording] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [recordingStream, setRecordingStream] = useState<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Dev Debugging states
  const [permission, setPermission] = useState('unknown');
  const [blobSize, setBlobSize] = useState(0);
  const [recordingTime, setRecordingTime] = useState(0);
  const [transcriptStatus, setTranscriptStatus] = useState('idle');
  const [chatRequestStatus, setChatRequestStatus] = useState('idle');
  const [speechStatus, setSpeechStatus] = useState('idle');
  const [latency, setLatency] = useState(0);
  const [lastError, setLastError] = useState<string | null>(null);

  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const logAether = (event: string, detail?: any) => {
    console.log(`[AETHER] ${event}`, detail !== undefined ? detail : '');
  };

  useEffect(() => {
    if (typeof window !== 'undefined' && navigator.mediaDevices && navigator.permissions) {
      navigator.permissions.query({ name: 'microphone' as any }).then(status => {
        setPermission(status.state);
        status.onchange = () => {
          setPermission(status.state);
        };
      }).catch(e => {
        logAether('Failed to query initial microphone permission state', e);
      });
    }
  }, []);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Voice synthesis states
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState<TimelineMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const speakText = (text: string) => {
    if (isMuted) {
      logAether('Speech bypassed: output is muted');
      return;
    }
    try {
      logAether('Cancelling active SpeechSynthesis speak queues');
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);

      utterance.onstart = () => {
        setIsSpeaking(true);
        setSpeechStatus('speaking');
        logAether('Speech synthesis output started', { textLength: text.length });
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        setSpeechStatus('finished');
        logAether('Speech synthesis output finished successfully');
        setMessages(prev => prev.map(m => ({ ...m, isSpeaking: false })));
      };

      utterance.onerror = (e) => {
        setIsSpeaking(false);
        setSpeechStatus('failed');
        logAether('ERROR: Speech synthesis output hit execution error', e);
        setMessages(prev => prev.map(m => ({ ...m, isSpeaking: false })));
      };

      const voices = window.speechSynthesis.getVoices();
      const defaultVoice = voices.find(v => v.default) || voices[0];
      logAether('Speech voice details selected', {
        voiceName: defaultVoice?.name || 'browser_default',
        lang: defaultVoice?.lang || 'unknown',
        systemVoicesAvailableCount: voices.length
      });

      window.speechSynthesis.speak(utterance);
      setMessages(prev => prev.map(m => m.role === 'assistant' ? { ...m, isSpeaking: m.text === text } : m));
    } catch (e) {
      logAether('ERROR: Speech synthesis initialization failed', e);
      setIsSpeaking(false);
      setSpeechStatus('failed');
    }
  };

  const stopSpeaking = () => {
    logAether('Manual speech cancel requested');
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setSpeechStatus('idle');
    setMessages(prev => prev.map(m => ({ ...m, isSpeaking: false })));
  };

  const replayMessage = (text: string) => {
    speakText(text);
  };

  const [timeStr, setTimeStr] = useState('');
  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setTimeStr(d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  async function ensureOrganization(token: string): Promise<string> {
    const organizations = await getOrganizations(token);
    if (!organizations[0]) throw new Error('No active workspace is available.');
    return organizations[0].id;
  }

  async function toggleConsent(enabled: boolean) {
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const organizationId = await ensureOrganization(token);
      const consent = await setVoiceConsent(
        token,
        organizationId,
        enabled,
        enabled ? retentionEnabled : false,
      );
      setCaptureEnabled(consent.capture_enabled);
      setRetentionEnabled(consent.retention_enabled);
      setStatus(enabled ? 'Voice capture consent granted.' : 'Voice capture consent withdrawn.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Consent update failed.');
    } finally {
      setBusy(false);
    }
  }

  async function startSession() {
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const organizationId = await ensureOrganization(token);
      const consent = await getVoiceConsent(token, organizationId);
      if (!consent.capture_enabled) throw new Error('Enable voice capture consent first.');
      const session = await createVoiceSession(token, organizationId, crypto.randomUUID());
      setSessionId(session.id);
      setStatus(`Voice session ${session.id} is active.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Session creation failed.');
    } finally {
      setBusy(false);
    }
  }

  async function submitTranscript(event?: FormEvent<HTMLFormElement>) {
    if (event) event.preventDefault();
    if (!sessionId || !transcript.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const organizationId = await ensureOrganization(token);

      // 1. Add User transcript to conversation list
      const userMsgId = crypto.randomUUID();
      setMessages(prev => [...prev, { id: userMsgId, role: 'user', text: transcript.trim() }]);

      // 2. Ensure Conversation ID exists
      let activeConvId = conversationId;
      if (!activeConvId) {
        const conv = await createConversation(token, organizationId, `Voice Session ${new Date().toLocaleDateString()}`);
        activeConvId = conv.id;
        setConversationId(activeConvId);
      }

      // 3. Send message to AI Assistant
      const chatResponse = await sendChatMessage(token, activeConvId, transcript.trim());

      // 4. Add Assistant's output to conversation list
      const assistantMsgId = crypto.randomUUID();
      setMessages(prev => [...prev, { id: assistantMsgId, role: 'assistant', text: chatResponse.content }]);

      // 5. Trigger client-side Speech Synthesis
      speakText(chatResponse.content);

      // 6. Compute command parses
      const command = await parseVoiceCommand(token, sessionId, organizationId, transcript.trim());

      // Categorize and preview payload if possible
      let parsedPayload = {};
      if (command.intent_type === 'workflow_run') {
        const wf = transcript.match(/\bworkflow\s+(\w+)/i);
        parsedPayload = { workflow_name: wf ? wf[1] : 'unknown' };
      } else if (command.intent_type === 'schedule_edit') {
        parsedPayload = { action: 'create', title: 'Schedule meeting', start_time: '09:00' };
      }

      setPending({
        confirmation_id: command.confirmation_id,
        intent_type: command.intent_type,
        transcript: command.transcript,
        payload: parsedPayload,
      });
      setStatus('Voice command parsed. Review action parameters.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Command parsing failed.');
    } finally {
      setBusy(false);
    }
  }

  async function decide(confirmed: boolean) {
    if (!pending || busy) return;
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const organizationId = await ensureOrganization(token);
      const result = await decideVoiceConfirmation(
        token,
        pending.confirmation_id,
        organizationId,
        confirmed,
      );
      setStatus(`Voice command ${result.decision}.`);
      setPending(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Confirmation failed.');
    } finally {
      setBusy(false);
    }
  }

  async function pollSessionStatus(token: string, sid: string, orgId: string) {
    let attempts = 0;
    const startT = Date.now();
    logAether('Starting transcription status polling for session', sid);
    const interval = setInterval(async () => {
      attempts++;
      setLatency(Date.now() - startT);
      if (attempts > 30) {
        clearInterval(interval);
        logAether('ERROR: Transcription polling timed out after 30 attempts');
        setError('Transcription timed out.');
        setLastError('Transcription timed out during polling.');
        setTranscriptStatus('failed');
        return;
      }
      try {
        logAether(`Polling attempt ${attempts} for session status`);
        const session = await getVoiceSession(token, sid, orgId);
        logAether(`Received poll status: ${session.status}`, session);

        if (session.transcript) {
          clearInterval(interval);
          logAether('Transcript received from server', session.transcript);
          setTranscript(session.transcript);
          setStatus('Transcription complete. Ready to parse.');
          setTranscriptStatus('complete');

          // Auto parse transcript and send to AI conversation logs
          setBusy(true);
          setChatRequestStatus('sending');
          const userMsgId = crypto.randomUUID();
          setMessages(prev => [...prev, { id: userMsgId, role: 'user', text: session.transcript || '' }]);

          let activeConvId = conversationId;
          if (!activeConvId) {
            logAether('No active conversation ID. Creating a new one...');
            const conv = await createConversation(token, orgId, `Voice Session ${new Date().toLocaleDateString()}`);
            activeConvId = conv.id;
            setConversationId(activeConvId);
            logAether('Created conversation ID', conv.id);
          }

          logAether('Sending transcript to chat API', { conversationId: activeConvId, prompt: session.transcript });
          const chatResponse = await sendChatMessage(token, activeConvId, session.transcript);
          logAether('Chat response received', chatResponse);
          setChatRequestStatus('done');

          const assistantMsgId = crypto.randomUUID();
          setMessages(prev => [...prev, { id: assistantMsgId, role: 'assistant', text: chatResponse.content }]);

          speakText(chatResponse.content);

          logAether('Parsing voice command for workflow/schedule intents');
          const command = await parseVoiceCommand(token, sid, orgId, session.transcript);
          logAether('Command intent parsed', command);

          let parsedPayload = {};
          if (command.intent_type === 'workflow_run') {
            const wf = session.transcript.match(/\bworkflow\s+(\w+)/i);
            parsedPayload = { workflow_name: wf ? wf[1] : 'unknown' };
          } else if (command.intent_type === 'schedule_edit') {
            parsedPayload = { action: 'create', title: 'Schedule meeting', start_time: '09:00' };
          }

          setPending({
            confirmation_id: command.confirmation_id,
            intent_type: command.intent_type,
            transcript: command.transcript,
            payload: parsedPayload,
          });
          setStatus('Voice command parsed. Review action parameters.');
          setBusy(false);
        } else if (session.status === 'failed') {
          clearInterval(interval);
          logAether('ERROR: Transcription status reported as failed by server');
          setError('Transcription failed on server.');
          setLastError('Server reported transcription generation failed.');
          setTranscriptStatus('failed');
        }
      } catch (err: any) {
        clearInterval(interval);
        logAether('ERROR: Failed during session poll checking', err);
        setError(`Failed to check transcription status: ${err.message}`);
        setLastError(err.message);
        setTranscriptStatus('failed');
      }
    }, 2000);
  }

  async function uploadAudio(file: File) {
    if (!sessionId || busy) {
      logAether('Upload canceled: sessionId missing or engine busy', { sessionId, busy });
      return;
    }
    setBusy(true);
    setError(null);
    setTranscriptStatus('uploading');
    logAether('Uploading audio file', { name: file.name, size: file.size, type: file.type });
    try {
      const token = await refreshAccessToken();
      const organizationId = await ensureOrganization(token);
      const buffer = await file.arrayBuffer();
      const bytes = new Uint8Array(buffer);
      let binary = '';
      for (const byte of bytes) binary += String.fromCharCode(byte);
      const content_base64 = btoa(binary);
      const extension = file.name.split('.').pop() ?? 'webm';

      logAether('Sending POST request to uploadVoiceAudio', { orgId: organizationId, ext: extension, length: content_base64.length });
      await uploadVoiceAudio(token, sessionId, organizationId, extension, content_base64, 30);

      logAether('Audio uploaded successfully for session', sessionId);
      setStatus('Audio uploaded for transcription. Polling status...');
      setTranscriptStatus('polling');
      void pollSessionStatus(token, sessionId, organizationId);
    } catch (cause: any) {
      logAether('Audio upload failed', cause);
      setError(cause instanceof Error ? cause.message : 'Audio upload failed.');
      setLastError(cause.message || 'Audio upload failed.');
      setTranscriptStatus('failed');
    } finally {
      setBusy(false);
    }
  }

  // HTML5 MediaRecorder Recording Functions
  async function startRecording() {
    setError(null);
    setLastError(null);
    setLiveTranscript('');
    setBlobSize(0);
    setRecordingTime(0);
    audioChunksRef.current = [];
    logAether('Recording requested');
    try {
      logAether('Requesting microphone permission');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setPermission('granted');
      setRecordingStream(stream);
      logAether('Microphone stream acquired');

      let mimeType = 'audio/webm';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/ogg';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = '';
        }
      }
      logAether('MediaRecorder mimeType selected', mimeType || 'browser default');

      const options = mimeType ? { mimeType } : undefined;
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          const currentSize = audioChunksRef.current.reduce((acc, chunk) => acc + chunk.size, 0);
          setBlobSize(currentSize);
          logAether(`Data available. Chunk size: ${event.data.size} bytes. Total size accumulated: ${currentSize} bytes`);
        }
      };

      mediaRecorder.onstop = async () => {
        logAether('MediaRecorder stopped');
        if (recordingIntervalRef.current) {
          clearInterval(recordingIntervalRef.current);
          recordingIntervalRef.current = null;
        }

        stream.getTracks().forEach((track) => track.stop());
        setRecordingStream(null);
        setIsRecording(false);
        setStatus('Processing recorded command...');

        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/webm' });
        setBlobSize(audioBlob.size);
        logAether('Audio Blob built', { size: audioBlob.size, type: audioBlob.type });

        if (audioBlob.size === 0) {
          logAether('WARNING: Created audio blob size is 0 bytes!');
          setLastError('Captured audio size is 0 bytes. Check mic hardware connection.');
        }

        const ext = mimeType ? mimeType.split('/')[1] : 'webm';
        const file = new File([audioBlob], `recording.${ext}`, { type: audioBlob.type });
        await uploadAudio(file);
      };

      mediaRecorder.start(250);
      setIsRecording(true);
      setTranscriptStatus('idle');
      logAether('MediaRecorder started');

      const startT = Date.now();
      recordingIntervalRef.current = setInterval(() => {
        setRecordingTime((Date.now() - startT) / 1000);
      }, 100);

      setStatus('Microphone active. Recording spoken instruction...');
    } catch (err: any) {
      logAether('Failed to start recording', err);
      setError(`Failed to access microphone: ${err.message}`);
      setLastError(err.message);
      setRecordingStream(null);
      setIsRecording(false);
      setPermission('denied');
    }
  }

  function stopRecording() {
    logAether('Stop recording manually requested');
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setRecordingStream(null);
    }
    setIsRecording(false);
  }

  return (
    <div className="relative min-h-screen text-slate-150 flex flex-col font-sans select-none overflow-x-hidden bg-[#05070a] p-6 lg:p-8">
      {/* Redesigned Cyberpunk Background HUD Grid & Scans */}
      <VoiceBackground />

      {/* Futuristic Glassmorphic Header */}
      <SystemHeader sessionId={sessionId} busy={busy} />

      {/* Main Grid Viewport Dashboard */}
      <main className="mx-auto flex-1 w-[92vw] max-w-[1800px] py-[32px] grid grid-cols-1 lg:grid-cols-[22%_56%_22%] gap-[28px] relative z-10">

        {/* Left Side Group Columns (Control Panel + Consent) */}
        <section className="flex flex-col gap-[24px]">
          <VoiceControls
            busy={busy}
            captureEnabled={captureEnabled}
            retentionEnabled={retentionEnabled}
            sessionId={sessionId}
            toggleConsent={toggleConsent}
            setRetentionEnabled={setRetentionEnabled}
            startSession={startSession}
            fileInputRef={fileInputRef}
            uploadAudio={uploadAudio}
          />
        </section>

        {/* Center Panel (Voice Core Visualizer Orb) */}
        <section className="flex flex-col gap-[24px]">
          <AetherCore
            stream={recordingStream}
            isRecording={isRecording}
            isThinking={busy}
            isSpeaking={isSpeaking}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={!sessionId || busy}
          />
        </section>

        {/* Right Panel (Gauges and System Telemetry) */}
        <section className="flex flex-col gap-[24px]">
          <TelemetryPanel
            isRecording={isRecording}
            hasSession={!!sessionId}
          />
        </section>
      </main>

      {/* Bottom Display Layout (Terminal & Conversation Timeline) */}
      <footer className="mx-auto w-[92vw] max-w-[1800px] pb-8 grid grid-cols-1 lg:grid-cols-2 gap-[28px] relative z-10">
        <VoiceTerminal
          transcript={transcript}
          setTranscript={setTranscript}
          busy={busy}
          sessionId={sessionId}
          submitTranscript={submitTranscript}
          pending={pending}
          decide={decide}
          status={status}
          error={error}
        />

        <ConversationTimeline
          messages={messages}
          isMuted={isMuted}
          setIsMuted={setIsMuted}
          isSpeaking={isSpeaking}
          onStopSpeaking={stopSpeaking}
          onReplay={replayMessage}
        />
      </footer>
    </div>
  );
}
