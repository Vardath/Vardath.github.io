-- Payment descriptions for REAL native transaction IDs. No menu/layout replacement.
-- Uses the optional, published UI Extensions callback already present in many installs.
-- Either extension may supply this identical file; register only once.
if _G.VardathNativeIncome then return _G.VardathNativeIncome end
local L = { receipts = {}, totals = {}, ids = {}, sequence = nil, installed = false }
_G.VardathNativeIncome = L
local ffi = require("ffi")
local C = ffi.C
local function nativeid(value) return tostring(ConvertStringTo64Bit(tostring(value))) end
-- Save data created by other extensions (or interrupted saves) can contain
-- partially imported receipt rows without sequence/ID keys. Never index a Lua
-- table with nil: keep the native game transaction log available regardless.
local function list(value) return type(value) == "table" and value or {} end
local function validreceipt(row)
    return type(row) == "table" and type(row[1]) == "number"
        and type(row[2]) == "number" and type(row[5]) == "number"
        and type(row[3]) == "string" and type(row[4]) == "string"
end
local function read()
    if not L.player then return end
    local sequence = tonumber(GetNPCBlackboard(L.player, "$vardath_income_seq")) or 0
    if L.sequence == sequence then return end
    L.receipts = list(GetNPCBlackboard(L.player, "$vardath_income"))
    L.totals = list(GetNPCBlackboard(L.player, "$vardath_income_totals"))
    L.bindings = list(GetNPCBlackboard(L.player, "$vardath_income_native_ids"))
    L.ids, L.byseq, L.claimed = {}, {}, {}
    for _, receipt in ipairs(L.receipts) do
        if validreceipt(receipt) then L.byseq[receipt[1]] = receipt end
    end
    for _, binding in ipairs(L.bindings) do
        if type(binding) == "table" and binding[1] ~= nil and
            type(binding[2]) == "number" and L.byseq[binding[2]] then
            local id = tostring(binding[1])
            L.ids[id] = binding[2]
            L.claimed[binding[2]] = id
        end
    end
    L.sequence = sequence
end
local function eventtype(receipt)
    return receipt[9] or (receipt[3] == "occupation_6" and "transfer" or "script_add")
end
local function matches(row, receipt)
    return type(receipt[2]) == "number" and type(receipt[5]) == "number"
        and row.eventtype == eventtype(receipt)
        and math.floor(row.money * 100 + 0.5) == math.floor(receipt[5] * 100 + 0.5)
        and math.abs(row.time - receipt[2]) <= 0.05
end
local function bind(receipt)
    if not validreceipt(receipt) then return false end
    if L.claimed[receipt[1]] then return true end
    local player = C.GetPlayerID()
    local count = C.GetNumTransactionLog(player, math.max(0, receipt[2] - 0.05), receipt[2] + 0.05)
    if count == 0 or count > 10000 then return false end
    local buf = ffi.new("TransactionLogEntry[?]", count)
    count = C.GetTransactionLog(buf, count, player, math.max(0, receipt[2] - 0.05), receipt[2] + 0.05)
    local found
    for i = 0, count - 1 do
        local row = buf[i]
        local id = nativeid(row.entryid)
        if id:sub(1, 1) ~= "-" and not L.ids[id] and matches({
            time = row.time, money = tonumber(row.money) / 100, eventtype = ffi.string(row.eventtype),
        }, receipt) then
            -- Ambiguous historical payments stay vanilla. Never guess or insert a row.
            if found then return false end
            found = id
        end
    end
    if not found then return false end
    L.ids[found], L.claimed[receipt[1]] = receipt[1], found
    local saved = {}
    for _, binding in ipairs(L.bindings) do
        if type(binding) == "table" and type(binding[2]) == "number" and L.byseq[binding[2]] then
            saved[#saved + 1] = binding
        end
    end
    saved[#saved + 1] = { found, receipt[1] }
    L.bindings = saved
    SetNPCBlackboard(L.player, "$vardath_income_native_ids", saved)
    return true
end
local function decorate(entry)
    read()
    if not L.player or not entry or entry.money <= 0 then return entry end
    if not Helper.transactionLogData or nativeid(Helper.transactionLogData.container) ~= nativeid(C.GetPlayerID()) then return entry end
    local id = nativeid(entry.entryid)
    local receipt = L.byseq and L.byseq[L.ids[id]]
    if not receipt and (entry.eventtype == "script_add" or entry.eventtype == "transfer") then
        local candidate
        for _, record in ipairs(L.receipts) do
            if validreceipt(record) and not L.claimed[record[1]] and matches(entry, record) then
                if candidate then return entry end
                candidate = record
            end
        end
        if candidate and bind(candidate) and L.claimed[candidate[1]] == id then receipt = candidate end
    end
    if not receipt or not matches(entry, receipt) then return entry end
    -- Mutate text fields only. Native IDs, money, event type, partners and graph stay intact.
    entry.eventtypename = receipt[4] .. " - " .. receipt[7]
    local text = receipt[8] or ""
    for _, total in ipairs(L.totals) do
        if type(total) == "table" and total[1] == receipt[3] and
            type(total[3]) == "number" and type(total[4]) == "number" then
            local amount = ConvertMoneyString and ConvertMoneyString(total[3], false, true, 0, true) or tostring(total[3])
            text = text .. "\n" .. receipt[4] .. " lifetime income: " .. amount .. " Cr (" .. total[4] .. " payments)"
            break
        end
    end
    entry.description = (entry.description ~= "" and entry.description .. "\n" or "") .. text
    return entry
end
function L.onEntry(entry)
    local ok, result = pcall(decorate, entry)
    -- A receipt failure must never prevent the vanilla transaction screen from opening.
    return ok and result or entry
end
function L.install(_, player)
    L.player = player or L.player or ConvertStringToLuaID(tostring(C.GetPlayerID()))
    pcall(read)
    if L.installed or not Helper or type(Helper.registerCallback) ~= "function" then return end
    if Helper.uix_isCallbackSupported and not Helper.uix_isCallbackSupported("createTransactionLog_on_before_adding_entry") then return end
    local ok = pcall(Helper.registerCallback, "createTransactionLog_on_before_adding_entry", L.onEntry, "VardathNativeIncome")
    L.installed = ok
end
function L.onPayment(_, player)
    L.install(nil, player)
    -- The optional UI annotation cannot throw out of a payment event. In
    -- particular, a malformed saved receipt must never abort the payment cue.
    if not pcall(read) then return end
    local receipt = L.byseq and L.byseq[L.sequence]
    if receipt and validreceipt(receipt) then pcall(bind, receipt) end
end
RegisterEvent("Vardath.NativeIncome.Install", L.install)
RegisterEvent("Vardath.NativeIncome.Payment", L.onPayment)
return L
