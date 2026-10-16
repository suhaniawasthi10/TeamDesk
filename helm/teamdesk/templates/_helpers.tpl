{{- define "teamdesk.labels" -}}
app.kubernetes.io/name: teamdesk
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{- define "teamdesk.backendImage" -}}
{{ .Values.image.backend }}:{{ required "A commit SHA image.tag is required" .Values.image.tag }}
{{- end }}
