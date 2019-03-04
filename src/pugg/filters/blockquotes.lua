-- Extracts all the content within BlockQuotes, and places the content in separate divs.


function Pandoc(doc)
    local hblocks = {}
    for i, el in pairs(doc.blocks) do
        if (el.t == "BlockQuote") then
           table.insert(hblocks, pandoc.Div(el.c, pandoc.Attr("", {}, {{"class", "card"}})))
        end
    end
    return pandoc.Pandoc(hblocks, doc.meta)
end


