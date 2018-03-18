-- grabs the comparisons in the UCLA format

select a.timestamp, b.name as img1name, c.name as img2name, a.win1, a.win2, a.tie from Comparisons a
inner join Images b on a.imageID_1 = b.imageHASH
inner join Images c on a.imageID_2 = c.imageHASH
where b.source = 'UCLA' and c.source = 'UCLA'
order by a.timestamp desc