-- Shared income section inside the main Transaction Log. Either extension can supply it.
if _G.VardathIncomeLedger then return _G.VardathIncomeLedger end
local L = { view = "payments", job = "all", page = 1, pagesize = 15, sequence = nil, entries = {}, totals = {} }
_G.VardathIncomeLedger = L
L.jobs = {
    { "occupation_1", "Galactic Escort Service" }, { "occupation_2", "Galactic Taxi Service" },
    { "occupation_3", "Station and Component Scanner" }, { "occupation_4", "Wormhole and Anomaly Mapper" },
    { "occupation_5", "Galactic Sightseeing Tour" }, { "occupation_6", "Autonomous Crystal Miner" },
    { "occupation_7", "Hostile Lure and Interception" }, { "occupation_8", "Asteroid Demolition" },
    { "occupation_9", "Fleet Morale Booster" }, { "occupation_10", "Traffic Control and Cargo Inspection" },
    { "occupation_11", "Emergency Ship Recruitment" }, { "occupation_12", "Trade Route Patrol" },
    { "builder_hire", "Builder hiring fee" }, { "builder_active", "Builder construction wages" },
    { "builder_standby", "Builder standby wages" }, { "builder_settlement", "Builder final settlement" },
}
local function id64(value) return ConvertStringTo64Bit(tostring(value)) end
local function read()
    if not L.player then return end
    local seq = GetNPCBlackboard(L.player, "$vardath_income_seq") or 0
    if L.sequence ~= seq then
        L.entries = GetNPCBlackboard(L.player, "$vardath_income") or {}
        L.totals = GetNPCBlackboard(L.player, "$vardath_income_totals") or {}
        L.sequence = seq
    end
end
local function money(value)
    if ConvertMoneyString then return ConvertMoneyString(value or 0, false, true, 0, true) .. " Cr" end
    return string.format("%.2f Cr", value or 0)
end
local function time(value)
    value = math.floor(tonumber(value) or 0)
    return string.format("%d:%02d:%02d", math.floor(value / 3600), math.floor(value / 60) % 60, value % 60)
end
function L.addPanel(frame, container, properties, refresh, first)
    if not L.player or tostring(id64(container)) ~= tostring(id64(L.player)) then return end
    read()
    local graph
    for i = first, #frame.content do
        local widget = frame.content[i]
        if widget.type == "table" and widget.numcolumns == 4 and widget.properties.tabOrder == 3 then graph = widget end
    end
    if not graph or not graph.rows[1] or not graph.rows[1][1] then return end
    -- Reserve room below the native account graph, keeping its data and native transaction list intact.
    local graphcell = graph.rows[1][1]
    if graphcell.type ~= "graph" then return end
    graphcell.properties.height = math.min(graphcell.properties.height, math.floor(properties.height * 0.40))
    local y = graph.properties.y + graph:getFullHeight() + Helper.borderSize * 2
    for i=first,#frame.content do
        local widget=frame.content[i]
        if widget.type=="table" and widget.properties.tabOrder==4 and widget.properties.x==graph.properties.x then
            widget.properties.y=y
            y=y+widget:getFullHeight()+Helper.borderSize*2
        end
    end
    local panel = frame:addTable(4, { tabOrder = 5, x = graph.properties.x, y = y, width = graph.properties.width,
        maxVisibleHeight = math.max(80, Helper.viewHeight - y - Helper.frameBorder), borderEnabled = true })
    panel:setColWidthPercent(1, 18)
    panel:setColWidthPercent(3, 18)
    panel:setColWidthPercent(4, 12)
    local row = panel:addRow(false, { fixed = true })
    row[1]:setColSpan(4):createText("Occupation & builder income", Helper.headerRowCenteredProperties)
    row = panel:addRow(true, { fixed = true })
    row[1]:setColSpan(2):createDropDown({ { id = "payments", text = "Individual payments" }, { id = "totals", text = "Lifetime earnings by job" } }, { startOption = L.view })
    row[1].handlers.onDropDownConfirmed = function (_, choice) L.view = choice; L.page = 1; refresh() end
    local options = { { id = "all", text = "All occupations and building" } }
    for _, job in ipairs(L.jobs) do options[#options + 1] = { id = job[1], text = job[2] } end
    row[3]:setColSpan(2):createDropDown(options, { startOption = L.job })
    row[3].handlers.onDropDownConfirmed = function (_, choice) L.job = choice; L.page = 1; refresh() end
    if L.view == "totals" then
        local totals = {}
        for _, entry in ipairs(L.totals) do totals[entry[1]] = entry end
        for _, job in ipairs(L.jobs) do
            if L.job == "all" or L.job == job[1] then
                local total = totals[job[1]] or { job[1], job[2], 0, 0 }
                row = panel:addRow(false, {})
                row[1]:setColSpan(2):createText(total[2])
                row[3]:createText(money(total[3]), { halign = "right" })
                row[4]:createText(tostring(total[4]) .. " paid", { halign = "right" })
            end
        end
    else
        local entries = {}
        for i = #L.entries, 1, -1 do
            if L.job == "all" or L.entries[i][3] == L.job then entries[#entries + 1] = L.entries[i] end
        end
        local pages = math.max(1, math.ceil(#entries / L.pagesize))
        L.page = math.max(1, math.min(L.page, pages))
        row = panel:addRow(true, { fixed = true })
        row[1]:createButton({ active = L.page > 1 }):setText("Previous")
        row[1].handlers.onClick = function () L.page = L.page - 1; refresh() end
        row[2]:setColSpan(2):createText("Page " .. L.page .. "/" .. pages .. " - game time; latest 5,000 payments")
        row[4]:createButton({ active = L.page < pages }):setText("Next")
        row[4].handlers.onClick = function () L.page = L.page + 1; refresh() end
        for i = (L.page - 1) * L.pagesize + 1, math.min(#entries, L.page * L.pagesize) do
            local entry = entries[i]
            row = panel:addRow(false, {})
            row[1]:createText(time(entry[2]))
            row[2]:createText(entry[4] .. " - " .. entry[7])
            row[3]:setColSpan(2):createText(money(entry[5]), { halign = "right" })
            row = panel:addRow(false, {})
            row[1]:setColSpan(4):createText(entry[8] or "")
        end
        if #entries == 0 then
            row = panel:addRow(false, {})
            row[1]:setColSpan(4):createText("No recorded payments for this selection since the income update.")
        end
    end
end
-- Native transaction IDs, times and money stay intact. Labels are a UI overlay;
-- unmatched verified credits appear as explicitly identified receipt rows in the same list.
function L.prepareNative(data)
    if not data or data._vardathPrepared then return end
    read()
    data._vardathPrepared = true
    data._vardathMatched, data._vardathUsed, data._vardathOverlap = {}, {}, {}
    local groups = {}
    for index, entry in ipairs(data.accountLogUnfiltered or {}) do
        if entry.money > 0 and (entry.ware or "") == "" and entry.eventtype ~= "trade" and entry.eventtype ~= "sellship" then
            local key = math.floor(entry.money * 100 + 0.5)
            groups[key] = groups[key] or {}
            groups[key][#groups[key] + 1] = { entry = entry, index = index }
        end
    end
    for amount, entries in pairs(groups) do
        table.sort(entries, function(a,b) return a.entry.time == b.entry.time and a.index < b.index or a.entry.time < b.entry.time end)
        local offset = 1
        while offset <= #entries do
            local last = offset
            while last < #entries and entries[last+1].entry.time - entries[offset].entry.time <= 0.25 do last = last + 1 end
            local records = {}
            for _, receipt in ipairs(L.entries) do
                if not data._vardathUsed[receipt[1]] and math.floor(receipt[5] * 100 + 0.5) == amount and math.abs(receipt[2] - entries[offset].entry.time) <= 0.25 then
                    records[#records+1] = receipt
                end
            end
            if #records == 1 and last == offset then
                for i, receipt in ipairs(records) do
                    local entry = entries[offset+i-1].entry
                    data._vardathMatched[tostring(entry.entryid)] = receipt
                    data._vardathUsed[receipt[1]] = true
                    entry.eventtypename = receipt[4] .. " - " .. receipt[7]
                    entry.description = receipt[8] or ""
                end
            else
                for _, receipt in ipairs(records) do data._vardathOverlap[receipt[1]] = true end
            end
            offset = last + 1
        end
    end
end
function L.renderNative(frame, container, refresh, first, requestedPage, properties)
    if not L.player or tostring(id64(container)) ~= tostring(id64(L.player)) then return end
    local data = Helper.transactionLogData
    if not data or not data.accountLogUnfiltered then return end
    L.prepareNative(data)
    local target, navigation, modern
    for i = first, #frame.content do
        local widget = frame.content[i]
        if widget.type == "table" then
            if widget.numcolumns == 9 and widget.properties.tabOrder == 1 then target = widget end
            if widget.numcolumns == 8 and widget.properties.tabOrder == 1 then navigation = widget end
            if widget.numcolumns == 7 and widget.properties.tabOrder == 2 then target = widget; modern = true end
        end
    end
    if not target then return end
    local zoom = Helper.transactionLogConfig and Helper.transactionLogConfig.zoomSteps[data.xZoom or 6]
    local current = tonumber(GetNPCBlackboard(L.player, "$vardath_income_now")) or 0
    for _, point in ipairs(data.graphdata or {}) do current = math.max(current, point.t or 0) end
    local starttime = math.max(0, current - 60 * (zoom and zoom.zoom or 60))
    local merged = {}
    local search = data.searchtext or ""
    local function matches(entry)
        if search == "" then return true end
        if L.originalSearch then return L.originalSearch(entry, search) end
        return (entry.eventtypename .. " " .. entry.description .. " " .. entry.partnername):lower():find(search:lower(),1,true) ~= nil
    end
    for _, entry in ipairs(data.accountLogUnfiltered) do if matches(entry) then merged[#merged+1] = entry end end
    for _, receipt in ipairs(L.entries) do
        if not data._vardathUsed[receipt[1]] and receipt[2] >= starttime and receipt[2] <= current + 1 then
            local entry = { vgoReceipt = true, vgoOverlap = data._vardathOverlap[receipt[1]], time = receipt[2], money = receipt[5],
                eventtypename = receipt[4] .. " - " .. receipt[7] .. " (verified receipt)", description = receipt[8] or "", partnername = "", ware = "", warename = "", partnername_secondary = "", sequence = receipt[1] }
            if matches(entry) then merged[#merged+1] = entry end
        end
    end
    table.sort(merged,function(a,b)
        if a.time == b.time then return (a.sequence or 0) > (b.sequence or 0) end
        return a.time > b.time
    end)
    local pagesize = Helper.transactionLogConfig and Helper.transactionLogConfig.transactionLogPage or 100
    local pages = math.max(1, math.ceil(#merged/pagesize))
    local page = math.max(1,math.min(requestedPage or data.curPage or 1,pages))
    local selectedId=modern and data.curEntryId or data.curEntry
    if selectedId then
        for i, entry in ipairs(merged) do if entry.entryid and tostring(entry.entryid)==tostring(selectedId) then page=math.ceil(i/pagesize); break end end
    end
    data.curPage, data.numPages = page, pages
    if modern and navigation and navigation.rows[1] and navigation.rows[1][1] then
        local title=navigation.rows[1][1].properties.text
        if type(title)=="string" then navigation.rows[1][1].properties.text=title:gsub("%(%d+%)$","(" .. #merged .. ")") end
    end
    -- Keep the vanilla title/search/paging widgets, then rebuild the same table's body.
    local kept, rows, header, showmore = {}, {}, nil, nil
    for _, row in ipairs(target.rows) do
        if row.properties and row.properties.fixed then rows[#rows+1]=row;kept[row]=true end
        if row.rowdata == "search" then header=row end
        if row.rowdata == "showmore" then showmore=row end
    end
    if modern and navigation then
        for _,row in ipairs(navigation.rows) do if row.rowdata=="search" or row[5]==data.pageEditBox then header=row end end
    end
    if frame.functionCells then
        local cells={}
        for _, cell in ipairs(frame.functionCells) do if not cell.row or cell.row.table~=target or kept[cell.row] then cells[#cells+1]=cell end end
        frame.functionCells=cells
    end
    target.rows=rows
    for i,row in ipairs(rows) do row.index=i end
    local function navigate(to) data.curEntry=nil;data.curEntryId=nil;data.curPage=to;refresh(1,1) end
    if header then
        local firstButton,prevButton,pageBox,nextButton,lastButton=4,5,6,8,9
        if modern then firstButton,prevButton,pageBox,nextButton,lastButton=3,4,5,6,7 end
        header[firstButton].properties.active=page>1;header[firstButton].handlers.onClick=function() navigate(1) end
        header[prevButton].properties.active=page>1;header[prevButton].handlers.onClick=function() navigate(page-1) end
        header[nextButton].properties.active=page<pages;header[nextButton].handlers.onClick=function() navigate(page+1) end
        header[lastButton].properties.active=page<pages;header[lastButton].handlers.onClick=function() navigate(pages) end
        header[pageBox]:setText(page .. " / " .. pages,{halign="center"})
        if modern and Helper.transactionLogConfig.pageSizeOptions then
            local options={}
            for _,size in ipairs(Helper.transactionLogConfig.pageSizeOptions) do
                options[#options+1]={id=tostring(size),text=tostring(size),icon="",displayremoveoption=false}
            end
            header[8].properties.options=options
            header[8].properties.active=#options>1
            header[8].properties.startOption=tostring(pagesize)
        end
    end
    local total = 0
    for i=(page-1)*pagesize+1,math.min(#merged,page*pagesize) do
        local entry=merged[i]
        if not entry.vgoOverlap then total=total+entry.money end
        local row=target:addRow(not entry.vgoReceipt and entry.entryid or false,{})
        local expanded=not entry.vgoReceipt and ((data.expandedEntries and data.expandedEntries[entry.entryid]) or (data.autoexpandedSearchEntries and data.autoexpandedSearchEntries[entry.entryid]))
        if not entry.vgoReceipt and entry.ware~="" then
            row[1]:createButton({}):setText(expanded and "-" or "+")
            row[1].handlers.onClick=function() Helper.buttonExpandTransactionEntry(entry.entryid,row.index,refresh) end
        end
        local amount=(entry.vgoOverlap and "Receipt: " or (entry.money>0 and "+" or "")) .. money(entry.money)
        local age=(modern and Helper.getPassedTimeShort or Helper.getPassedTime)
        age=age and age(entry.time) or time(entry.time)
        if modern then
            local label=entry.eventtypename
            if not entry.vgoReceipt and not data._vardathMatched[tostring(entry.entryid)] then
                label=(entry.partnericonstring or "") .. ((entry.partnername or "")~="" and entry.partnername or entry.eventtypename)
            end
            if entry.eventicon and entry.eventicon~="" then row[2]:createIcon(entry.eventicon,{}) end
            row[3]:createText(label,{mouseOverText=entry.description})
            if entry.warename and entry.warename~="" then row[4]:createText(entry.warename,{halign="right"}) end
            row[5]:createText(amount,{halign="right"})
            row[6]:createText(age,{halign="right"})
        else
            row[2]:createText((entry.partnername~="" and (entry.partnername .. " - ") or "") .. entry.eventtypename,{mouseOverText=entry.description})
            row[3]:setColSpan(4):createText(age,{halign="right"})
            row[7]:setColSpan(3):createText(amount,{halign="right"})
        end
        if selectedId and entry.entryid and tostring(entry.entryid)==tostring(selectedId) and type(target.setSelectedRow)=="function" then target:setSelectedRow(row.index) end
        if data.topRowId and entry.entryid and tostring(entry.entryid)==tostring(data.topRowId) and type(target.setTopRow)=="function" then target:setTopRow(row.index) end
        if entry.vgoReceipt then
            local detail=target:addRow(false,{})
            detail[modern and 3 or 2]:setColSpan(modern and 5 or 8):createText(entry.description .. (entry.vgoOverlap and " - Possible native entry in this list; this receipt is not an additional transfer." or ""),{wordwrap=true})
        elseif expanded then
            if modern then
                local detail=target:addRow({entry.entryid,true},{})
                local name=entry.partnername_secondary or ""
                if entry.partner_secondary and entry.partner_secondary~=0 and Helper.getNameAndIdString then name=Helper.getNameAndIdString(entry.partner_secondary) end
                detail[3]:createText((entry.partnericonstring_secondary or "") .. name,{mouseOverText=entry.description})
                if entry.warename and entry.warename~="" then
                    detail[4]:createText(tostring(entry.amount or 0) .. "x",{halign="right"})
                    detail[5]:createText(money(entry.price),{halign="right"})
                end
            else
                target:addRow(false,{})[2]:setColSpan(8):createText(entry.description,{wordwrap=true})
            end
        end
    end
    if #merged==0 then target:addRow(false,{})[modern and 3 or 2]:setColSpan(modern and 5 or 8):createText("No transactions in this time range.") end
    if modern and page<pages then
        local more=target:addRow("showmore",{})
        more[1]:setColSpan(7):createButton({}):setText("Next page")
        more[1].handlers.onClick=function() navigate(page+1) end
    elseif not modern and showmore then
        showmore.index=#target.rows+1;target.rows[#target.rows+1]=showmore
        showmore[1].handlers.onClick=function() Helper.buttonTransactionLogZoom(1,refresh) end
    end
    for i=first,#frame.content do
        local widget=frame.content[i]
        if widget.type=="table" and widget.properties.tabOrder==0 and widget.numcolumns==(modern and 7 or 2) then
            local row=widget.rows[#widget.rows]
            local column=modern and 5 or 2
            if row and row[column] then row[column].properties.text=(total>0 and "+" or "") .. money(total) end
            if properties then
                local height=widget:getFullHeight()
                local available=properties.y and properties.y+properties.height-target.properties.y-height-Helper.frameBorder or properties.height-height-Helper.frameBorder
                widget.properties.y=target.properties.y+math.min(available,target:getFullHeight())
                target.properties.maxVisibleHeight=widget.properties.y-target.properties.y
            end
        end
    end
end

function L.install(_, player)
    if player then L.player = ConvertStringToLuaID(tostring(player)) end
    if not Helper or type(Helper.createTransactionLog) ~= "function" or Helper.createTransactionLog == L.hook then return end
    if type(Helper.transactionLogSearchHelper) == "function" and Helper.transactionLogSearchHelper ~= L.searchHook then
        local originalSearch = Helper.transactionLogSearchHelper
        L.originalSearch = originalSearch
        L.searchHook = function(entry, text)
            if L.player and L.activeContainer and tostring(id64(L.player))==tostring(id64(L.activeContainer)) then L.prepareNative(Helper.transactionLogData) end
            return originalSearch(entry, text)
        end
        Helper.transactionLogSearchHelper = L.searchHook
    end
    local original = Helper.createTransactionLog
    L.hook = function (frame, container, properties, refresh, selection, ...)
        local first = #frame.content + 1
        local requestedPage = Helper.transactionLogData and Helper.transactionLogData.curPage or 1
        local previousContainer=L.activeContainer
        L.activeContainer=container
        local result = original(frame, container, properties, refresh, selection, ...)
        L.activeContainer=previousContainer
        if not frame.vardathIncomeAdded then
            L.renderNative(frame, container, refresh, first, requestedPage, properties)
            L.addPanel(frame, container, properties, refresh, first)
            frame.vardathIncomeAdded = true
        end
        return result
    end
    Helper.createTransactionLog = L.hook
end
RegisterEvent("Vardath.IncomeLedger.Install", L.install)
L.install()
return L
