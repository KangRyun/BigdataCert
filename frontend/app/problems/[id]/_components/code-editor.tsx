"use client";

import Editor from "@monaco-editor/react";

interface Props {
  value: string;
  onChange: (next: string) => void;
  onSubmit: () => void;
}

export default function CodeEditor({ value, onChange, onSubmit }: Props) {
  return (
    <Editor
      height="100%"
      defaultLanguage="python"
      language="python"
      theme="vs-dark"
      value={value}
      onChange={(v) => onChange(v ?? "")}
      options={{
        fontSize: 14,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        tabSize: 4,
        insertSpaces: true,
        wordWrap: "on",
        automaticLayout: true,
      }}
      onMount={(editor, monaco) => {
        editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, onSubmit);
      }}
      loading={<div className="editor-loading">에디터를 불러오는 중…</div>}
    />
  );
}
