# JANUS / DeepThorT — Missing Ability Register

**Baseline:** V72, source commit `5042db98ab4e54ae4c138cfe6ef33b74d23df972` (Linux and Windows CI passed, [run 45897512810](https://github.com/Vardath/Vardath.github.io/actions/runs/45897512810)). **Register revision:** 27 November 2026. **Total: 210 entries.**

## Purpose and interpretation

This is the owner's requested consolidated missing-capability register, reordered from easiest to hardest estimated implementation within the existing JANUS application. It preserves every original entry and its original ID from the capability comparison, including entries whose complete integration was not established and integrated acceptance testing (an outstanding validation task rather than a product feature).

The rank describes estimated engineering effort, not value, urgency, user priority, guaranteed feasibility, or an instruction to begin implementation. Relative positions within an effort band are approximate; prerequisites may change the order. It is a qualitative estimate, not a timed benchmark. Before implementation, inspect the current source and verify whether the capability is already present, partial, intentionally restricted, or genuinely missing. Reuse existing capabilities rather than duplicate them. A working third-party tool is not equivalent to integrated, validated autonomous operation.

Preserve the original JANUS and Sentinel recursive societies, five assigned local intelligence models, existing project/approval/verification mechanisms and gaming-aware shared 50% CPU and up-to-65% RAM-sized aggregate commit ceiling. No automatic permission expansion, model replacement, cloud inference, purchase, backend change or resource-cap increase is authorized by this register. Secure external account connections and publishing/deployment require separate authorization; resource-intensive local multimedia/model capabilities may need alternative compatible tools or future hardware. Do not describe an isolated working directory as a security sandbox. Existing local machine limitations and native acceptance must be respected.

## Effort bands (easiest to hardest)

- **A — Low effort: bounded local extensions:** Existing Python/CLI libraries and established project grants, data formats, validation and native tool adapters. Mostly one capability boundary at a time; not zero effort. (34 entries.)
- **B — Moderate effort: new adapters and durable workflows:** New integrations, local libraries, structured APIs, scheduling or evidence checks. Requires real end-to-end tests, setup, dependencies and permissions. Reuses the current worker architecture. (65 entries.)
- **C — Substantial effort: integrated application workflows:** Cross-application coordination, session handling, secure external services, complex UI, or multi-stage verification. Several prerequisites must be integrated; broader workflows require tests beyond individual adapters. (82 entries.)
- **D — High effort: complex model/production and infrastructure integrations:** Specialist models, native dependencies, high-quality generation, OS integration, secure deployment or resource-sensitive operation. Local availability and model suitability must be demonstrated; no cloud inference or cap changes implied. (29 entries.)

## Single ranked register

| Ease rank | Original ID | Effort | Ability / feature |
|---:|---:|:---:|---|
| 1 | 45 | A | Git commit management |
| 2 | 46 | A | Git branch management |
| 3 | 47 | A | Git worktree management |
| 4 | 207 | A | Automated dependency security auditing |
| 5 | 44 | A | Software security vulnerability scanning |
| 6 | 69 | A | Completing interactive PDF forms |
| 7 | 70 | A | Creating fillable PDF forms |
| 8 | 68 | A | Editing existing PDF documents |
| 9 | 71 | A | Editing existing spreadsheets |
| 10 | 72 | A | Editing existing presentations |
| 11 | 73 | A | Presentation template application |
| 12 | 77 | A | Interactive data tables |
| 13 | 78 | A | Interactive charts and visualisations |
| 14 | 136 | A | Musical tempo detection |
| 15 | 137 | A | Musical key detection |
| 16 | 153 | A | Audio noise reduction |
| 17 | 163 | A | Normal-map generation |
| 18 | 161 | A | Automatic UV unwrapping |
| 19 | 167 | A | 3D printing preparation |
| 20 | 100 | A | Multi-image composition |
| 21 | 90 | A | Image background removal |
| 22 | 91 | A | Image background replacement |
| 23 | 13 | A | Optical character recognition (OCR) |
| 24 | 7 | A | Scheduled task execution |
| 25 | 6 | A | User-defined recurring tasks |
| 26 | 25 | A | Website change monitoring |
| 27 | 9 | A | Continuous monitoring of user-defined conditions |
| 28 | 8 | A | Event-triggered workflows |
| 29 | 24 | A | Automated price monitoring |
| 30 | 22 | A | Current news gathering |
| 31 | 17 | A | Search-engine result interpretation |
| 32 | 16 | A | General internet search |
| 33 | 21 | A | Scientific citation verification |
| 34 | 20 | A | Academic literature discovery |
| 35 | 18 | B | Website crawling |
| 36 | 12 | B | Semantic vector embeddings |
| 37 | 14 | B | Handwritten document recognition |
| 38 | 74 | B | Document layout inspection |
| 39 | 75 | B | Automated visual document quality verification |
| 40 | 79 | B | Predictive modelling |
| 41 | 80 | B | Time-series forecasting |
| 42 | 82 | B | Jupyter notebook integration |
| 43 | 83 | B | Live database connections |
| 44 | 81 | B | Business intelligence |
| 45 | 84 | B | Connected business-data analysis |
| 46 | 54 | B | Database migration management |
| 47 | 41 | B | Language-server integration |
| 48 | 43 | B | Inline code completion |
| 49 | 48 | B | Pull request creation |
| 50 | 49 | B | Pull request review |
| 51 | 50 | B | Automated merge conflict resolution |
| 52 | 65 | B | OAuth authentication and external account connections |
| 53 | 182 | B | GitHub account integration |
| 54 | 67 | B | Webhook integration |
| 55 | 203 | B | OpenAI-compatible external developer API |
| 56 | 10 | B | Remote task submission |
| 57 | 11 | B | Cross-device notifications |
| 58 | 2 | B | Microphone input |
| 59 | 140 | B | Speech-to-text conversion |
| 60 | 141 | B | Audio transcription |
| 61 | 174 | B | Meeting transcription |
| 62 | 144 | B | Expressive neural speech synthesis |
| 63 | 143 | B | Speaker diarisation |
| 64 | 142 | B | Speaker identification |
| 65 | 152 | B | Audio restoration |
| 66 | 154 | B | Audio source isolation |
| 67 | 131 | B | Musical stem separation |
| 68 | 132 | B | Instrument isolation |
| 69 | 135 | B | Audio-to-MIDI transcription |
| 70 | 133 | B | Automated audio mixing |
| 71 | 134 | B | Automated audio mastering |
| 72 | 160 | B | Automatic mesh retopology |
| 73 | 162 | B | Automatic texture mapping |
| 74 | 164 | B | Automatic character rigging |
| 75 | 166 | B | Animation retargeting |
| 76 | 95 | B | Image super-resolution and upscaling |
| 77 | 94 | B | Image restoration |
| 78 | 93 | B | Image colourisation |
| 79 | 92 | B | Image style transfer |
| 80 | 85 | B | Image-to-image generation |
| 81 | 86 | B | Image inpainting |
| 82 | 87 | B | Image outpainting |
| 83 | 88 | B | Image object removal |
| 84 | 89 | B | Image object replacement |
| 85 | 97 | B | Pose-controlled image generation |
| 86 | 98 | B | Depth-controlled image generation |
| 87 | 99 | B | Sketch-to-image conversion |
| 88 | 101 | B | Photorealistic product mockup generation |
| 89 | 102 | B | Layer-aware image editing |
| 90 | 103 | B | Visual multimedia generation workflow graphs |
| 91 | 107 | B | Existing video interpretation |
| 92 | 111 | B | Video motion tracking |
| 93 | 113 | B | Video frame interpolation |
| 94 | 114 | B | Video upscaling |
| 95 | 120 | B | Multitrack video editing timelines |
| 96 | 121 | B | Automatic video highlight extraction |
| 97 | 62 | B | Android emulator operation |
| 98 | 55 | B | Container creation and management |
| 99 | 210 | B | Integrated five-model acceptance testing |
| 100 | 19 | C | Autonomous deep research |
| 101 | 23 | C | Comprehensive market research |
| 102 | 31 | C | Webpage element inspection |
| 103 | 30 | C | Autonomous website navigation |
| 104 | 32 | C | Website interaction and control selection |
| 105 | 35 | C | Browser-based file downloads |
| 106 | 34 | C | Browser-based file uploads |
| 107 | 33 | C | Automated online form completion |
| 108 | 37 | C | Browser developer tools integration |
| 109 | 38 | C | General browser automation |
| 110 | 36 | C | Operation of authenticated browser sessions |
| 111 | 26 | C | Research using authenticated websites |
| 112 | 28 | C | Mouse control |
| 113 | 29 | C | Keyboard control |
| 114 | 27 | C | Graphical application operation |
| 115 | 4 | C | Live screen interpretation |
| 116 | 3 | C | Live camera interpretation |
| 117 | 60 | C | Game controller input simulation |
| 118 | 58 | C | Visual gameplay testing |
| 119 | 59 | C | Autonomous game playing and testing |
| 120 | 61 | C | Automated game balancing |
| 121 | 57 | C | Unreal Engine integration |
| 122 | 42 | C | Integrated development environment (IDE) integration |
| 123 | 51 | C | Continuous integration and deployment (CI/CD) management |
| 124 | 52 | C | Automated software deployment |
| 125 | 56 | C | Remote software development environments |
| 126 | 63 | C | Automated game distribution |
| 127 | 64 | C | Plugin marketplace and management |
| 128 | 66 | C | Visual workflow builder |
| 129 | 76 | C | Collaborative document editing |
| 130 | 168 | C | Email reading and searching |
| 131 | 169 | C | Email sending |
| 132 | 170 | C | Automated inbox organisation |
| 133 | 171 | C | Calendar management |
| 134 | 172 | C | Appointment scheduling |
| 135 | 173 | C | Contact management |
| 136 | 175 | C | Cloud storage integration |
| 137 | 176 | C | Google Drive integration |
| 138 | 177 | C | Google Workspace document creation and editing |
| 139 | 178 | C | Microsoft 365 integration |
| 140 | 179 | C | Slack integration |
| 141 | 180 | C | Discord integration |
| 142 | 181 | C | Telegram integration |
| 143 | 183 | C | Social media publishing |
| 144 | 184 | C | Social media analytics |
| 145 | 185 | C | Website content management |
| 146 | 186 | C | Customer relationship management (CRM) |
| 147 | 187 | C | Customer-support automation |
| 148 | 188 | C | E-commerce management |
| 149 | 189 | C | Accounting software integration |
| 150 | 190 | C | Inventory management integration |
| 151 | 191 | C | External project management platform integration |
| 152 | 192 | C | Online shopping assistance |
| 153 | 193 | C | Travel planning using live information |
| 154 | 194 | C | External booking system integration |
| 155 | 195 | C | Cross-application business automation |
| 156 | 138 | C | Digital audio workstation (DAW) operation |
| 157 | 139 | C | Audio plugin development |
| 158 | 105 | C | Image-to-motion-video generation |
| 159 | 109 | C | Video background replacement |
| 160 | 110 | C | Video style transfer |
| 161 | 108 | C | Video object removal |
| 162 | 112 | C | Camera motion generation |
| 163 | 115 | C | Lip synchronisation |
| 164 | 119 | C | Audio-driven animation |
| 165 | 122 | C | Video dubbing |
| 166 | 149 | C | Automatic multilingual dubbing |
| 167 | 148 | C | Real-time speech translation |
| 168 | 1 | C | Real-time spoken conversation |
| 169 | 155 | C | Real-time conversational voice agents |
| 170 | 147 | C | Voice transformation |
| 171 | 145 | C | Voice cloning with consent |
| 172 | 146 | C | Custom voice design |
| 173 | 150 | C | Sound-effect generation |
| 174 | 151 | C | Ambient sound generation |
| 175 | 129 | C | Singing voice generation |
| 176 | 130 | C | Vocal harmony generation |
| 177 | 165 | C | Motion capture |
| 178 | 159 | C | Automated photogrammetry |
| 179 | 5 | C | Autonomous creation and configuration of specialist AI agents |
| 180 | 208 | C | User-authorised autonomous self-installation |
| 181 | 209 | C | Complete application rollback and restoration |
| 182 | 96 | D | Consistent character generation across images |
| 183 | 104 | D | Neural text-to-video generation |
| 184 | 106 | D | Video-to-video generation |
| 185 | 116 | D | Talking avatar generation |
| 186 | 117 | D | Digital human presenter generation |
| 187 | 118 | D | Consistent animated character generation |
| 188 | 123 | D | Full audio song generation with vocals |
| 189 | 124 | D | Audio-to-music generation |
| 190 | 125 | D | Melody-to-song generation |
| 191 | 126 | D | Reference-guided music generation |
| 192 | 127 | D | Song continuation |
| 193 | 128 | D | Individual song section replacement and editing |
| 194 | 156 | D | Neural text-to-3D generation |
| 195 | 157 | D | Image-to-3D reconstruction |
| 196 | 158 | D | Multi-view 3D reconstruction |
| 197 | 196 | D | GPU-accelerated text inference |
| 198 | 198 | D | AI model format conversion |
| 199 | 197 | D | AI model quantisation |
| 200 | 201 | D | AI model merging |
| 201 | 200 | D | LoRA training |
| 202 | 199 | D | AI model fine-tuning |
| 203 | 15 | D | Model fine-tuning from accumulated experience |
| 204 | 53 | D | Cloud infrastructure provisioning |
| 205 | 39 | D | Remote computer control |
| 206 | 40 | D | Virtual computer environments |
| 207 | 206 | D | Virtual machine isolation |
| 208 | 205 | D | Operating-system-level execution sandboxing |
| 209 | 204 | D | Multi-user AI service hosting |
| 210 | 202 | D | Distributed inference |

## Maintenance

- Original IDs are stable across revisions; update rank and evidence when actual development effort is known.
- Track source-backed implementation, integration and acceptance independently. Do not remove an entry merely because a tool exists or a model claims it can perform the task.
- The owner determines what to implement and when. This register does not modify the existing workflow continuation plan or supersede any owner-approved development instruction.
- The original capability comparison was a representative market survey, not exhaustive certification of every AI product or every implementation. No claim is made that all items can run within the current hardware budget.
