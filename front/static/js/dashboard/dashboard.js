(() => {
  if (!window.Chart || !window.dashboardData) return;
  const palette = ['#36765b','#2767a8','#bb6840','#b08a3d','#657d91','#789381','#8b9095'];
  const d = window.dashboardData;
  new Chart(document.getElementById('statusChart'), {type:'doughnut',data:{labels:d.statusLabels,datasets:[{data:d.statusValues,backgroundColor:palette,borderWidth:0,hoverOffset:5}]},options:{cutout:'73%',maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#16233a',padding:12,cornerRadius:8}}}});
  const legend = document.getElementById('statusLegend');
  d.statusLabels.forEach((label,i)=>{const node=document.createElement('span');node.innerHTML=`<i style="background:${palette[i]}"></i>${label}<b>${d.statusValues[i]}</b>`;legend.appendChild(node);});
  new Chart(document.getElementById('activityChart'), {type:'line',data:{labels:d.activityLabels,datasets:[{data:d.activityValues,borderColor:'#2767a8',backgroundColor:'rgba(39,103,168,.08)',fill:true,tension:.22,pointRadius:3,pointHoverRadius:5,pointBackgroundColor:'#fff',pointBorderWidth:2,pointBorderColor:'#2767a8'}]},options:{maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},border:{display:false},ticks:{color:'#687789',font:{family:'Segoe UI'}}},y:{beginAtZero:true,grid:{color:'#e6ebf0'},border:{display:false},ticks:{precision:0,color:'#687789',font:{family:'Segoe UI'}}}}}});
})();
