"""Process-local privacy and noninteractive native startup policy for Triad."""
def disable_openvino_telemetry():
    # The pinned runtime depends on openvino-telemetry. Its opt-out CLI may
    # itself send a final analytics event; avoid touching user-wide consent
    # settings or making network calls from the private inference worker.
    from openvino_telemetry.utils.opt_in_checker import OptInChecker, ConsentCheckResult
    from openvino_telemetry.utils.sender import TelemetrySender
    def declined(self,*args,**kwargs):
        return ConsentCheckResult.DECLINED
    def discard(self,*args,**kwargs):
        return None
    OptInChecker.check=declined
    TelemetrySender.send=discard
