import * as T from 'three';
export const LOCATIONS={tando:[180,-190],marina:[340,100],crossing:[-30,170],jebu:[-330,170],nue:[-170,-240]};
export const NAMES={tando:'탄도항 · 풍력발전기',marina:'전곡항 · 카페',crossing:'제부도 바닷길',jebu:'제부도 · 저녁',nue:'누에섬 · 이번엔 바라보기'};
export function createCoast(){
 const root=new T.Group(),geo=new T.BoxGeometry(1,1,1),cyl=new T.CylinderGeometry(1,1,1,12),ball=new T.IcosahedronGeometry(1,1),mats=new Map(),buckets=new Map(),rotors=[],lights=[];
 let seed=21;const rnd=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
 const mat=c=>{if(!mats.has(c))mats.set(c,new T.MeshStandardMaterial({color:c,roughness:.9,flatShading:true}));return mats.get(c);};
 function put(g,x,y,z,sx,sy,sz,c,ry=0){const k=(g===geo?'b':g===cyl?'c':'s')+c;if(!buckets.has(k))buckets.set(k,{g,c,items:[]});const o=new T.Object3D();o.position.set(x,y,z);o.scale.set(sx,sy,sz);o.rotation.y=ry;o.updateMatrix();buckets.get(k).items.push(o.matrix.clone());}
 const box=(x,y,z,w,h,d,c,r=0)=>put(geo,x,y,z,w,h,d,c,r);
 function segment(a,b,w,h,c){const dx=b[0]-a[0],dz=b[1]-a[1],len=Math.hypot(dx,dz);box((a[0]+b[0])/2,h/2+3,(a[1]+b[1])/2,w,h,len,c,Math.atan2(dx,dz));}
 function tree(x,z,s=1){box(x,12*s,z,3*s,18*s,3*s,'#806c49');put(ball,x,28*s,z,12*s,18*s,12*s,'#72916c');put(ball,x+5*s,34*s,z,9*s,12*s,9*s,'#8d9f6d');}
 function house(x,z,w=24,h=24,d=22,color='#eadbc2'){box(x,h/2+9,z,w,h,d,color);box(x,h+11,z,w+3,4,d+4,'#a57559');for(let q=-w/2+5;q<w/2-2;q+=8)for(let y=18;y<h+3;y+=10){box(x+q,y,z+d/2+.4,4,5,1,'#547774');}box(x,15,z+d/2+.8,5,11,1,'#b39366');}
 function boat(x,z,s=1,angle=0){const group=new T.Group();const hull=new T.Mesh(new T.CylinderGeometry(3*s,2*s,20*s,5),mat('#f4edda'));hull.rotation.x=Math.PI/2;hull.position.y=3*s;group.add(hull);const cabin=new T.Mesh(new T.BoxGeometry(4*s,3*s,6*s),mat('#527b7b'));cabin.position.set(0,6*s,1*s);group.add(cabin);const mast=new T.Mesh(new T.CylinderGeometry(.3*s,.3*s,23*s,5),mat('#e9debd'));mast.position.set(0,17*s,0);group.add(mast);const sail=new T.Shape();sail.moveTo(.4*s,0);sail.lineTo(.4*s,18*s);sail.lineTo(7*s,0);const cloth=new T.Mesh(new T.ShapeGeometry(sail),new T.MeshStandardMaterial({color:'#eee9d0',side:T.DoubleSide}));cloth.position.set(0,8*s,0);group.add(cloth);group.position.set(x,0,z);group.rotation.y=angle;root.add(group);}
 // Ocean and two distinct coastlines. The model is illustrative, not a navigation map.
 const waterMaterial=new T.MeshStandardMaterial({color:'#90b7b1',roughness:.6,metalness:.12});const water=new T.Mesh(new T.PlaneGeometry(3000,3000),waterMaterial);water.rotation.x=-Math.PI/2;water.position.y=-1;water.receiveShadow=true;root.add(water);
 const land=new T.Shape();land.moveTo(90,-470);land.lineTo(700,-470);land.lineTo(700,570);land.lineTo(430,520);land.quadraticCurveTo(400,330,300,290);land.quadraticCurveTo(285,210,280,60);land.quadraticCurveTo(270,-30,100,-170);land.quadraticCurveTo(280,-260,90,-470);
 const lg=new T.ExtrudeGeometry(land,{depth:14,bevelEnabled:true,bevelSegments:1,steps:1,bevelSize:7,bevelThickness:5});lg.rotateX(Math.PI/2);const lm=new T.Mesh(lg,mat('#c6ceab'));lm.position.y=5;lm.receiveShadow=true;root.add(lm);
 // Use broad landscaped plazas to keep the stylized harbor above the sea.
 box(240,4,-185,260,8,190,'#c8d0ae');box(380,4,105,180,8,240,'#d4d1b7');
 put(cyl,-330,0,170,154,20,130,'#b4b79a');put(cyl,-330,7,170,144,12,120,'#cbd0a8');put(ball,-340,18,128,95,30,72,'#a9bb90');
 put(ball,-175,4,-260,73,26,49,'#a5b89b');put(ball,-155,19,-264,36,35,32,'#94ab8c');
 // Island lookout and lighthouse.
 put(cyl,-174,54,-260,8,42,8,'#f1e8cf');put(cyl,-174,77,-260,11,5,11,'#805d44');box(-174,83,-260,12,10,12,'#4f7370');put(cyl,-174,90,-260,10,4,10,'#bb7350');
 // Submerged-looking pedestrian causeway, separate from the vehicle road.
 segment([145,-185],[-130,-260],12,1,'#aaae98');
 // Vehicle causeway, markings and guard posts.
 const a=[320,260],b=[-275,195];segment(a,b,26,4,'#697d77');segment([a[0]+1,a[1]+13],[b[0]+1,b[1]+13],1,5,'#e4dbb9');segment([a[0]-1,a[1]-13],[b[0]-1,b[1]-13],1,5,'#e4dbb9');for(let i=0;i<28;i++){let t=i/28,x=a[0]+(b[0]-a[0])*t,z=a[1]+(b[1]-a[1])*t;box(x,7.1,z,9,.3,1,'#e8d099',-.11);for(const q of [-15,15]){box(x,9,z+q,1.3,10,1.3,'#eae1c3');}}
 // Mainland roads, harbor parking, lined spaces.
 box(300,11,-25,27,2,670,'#9fa993');box(270,11,-125,320,2,27,'#9fa993');box(196,11,-155,102,1,57,'#acb39e');for(let x=155;x<240;x+=15)box(x,11.7,-155,.7,.3,48,'#eeebd3');
 // Three iconic turbines with genuinely rotating blade assemblies.
 for(let i=0;i<3;i++){const x=35-i*59,z=-190-i*16;put(cyl,x,39,z,3.1,76,3.1,'#f3efde');box(x,81,z,8,5,9,'#e9e6d9');const rotor=new T.Group();rotor.position.set(x,81,z+6);for(let n=0;n<3;n++){const g=new T.Group();g.rotation.z=n*Math.PI*2/3;const blade=new T.Mesh(new T.BoxGeometry(3,36,1.4),mat('#f7f0dc'));blade.position.y=20;g.add(blade);rotor.add(g);}const hub=new T.Mesh(new T.SphereGeometry(3.2,8,6),mat('#d8ddcc'));rotor.add(hub);root.add(rotor);rotors.push(rotor);}
 // Marina pontoon piers and rows of yachts.
 segment([250,15],[250,185],8,4,'#d1bb8f');segment([250,185],[320,185],8,4,'#d1bb8f');for(const z of [30,90,150]){segment([250,z],[125,z],6,4,'#d5c29c');for(let x=145;x<211;x+=21){boat(x,z-14,.65,.08);boat(x,z+14,.65,.08);}}
 house(340,90,78,37,44,'#ecdfc4');box(340,50,90,84,4,50,'#63847b');for(let x=308;x<=371;x+=10)box(x,33,113,7,19,1,'#628c89');box(340,14,124,94,3,22,'#c7b795');for(let x=305;x<385;x+=20){put(cyl,x,18,130,5,2,5,'#f0dcb2');box(x,13,130,1,10,1,'#8b7654');}box(340,45,113.8,42,7,1,'#ad714c');
 // Village fabric, island coastal drive and boardwalk.
 for(let i=0;i<26;i++){const x=340+rnd()*220,z=-410+rnd()*420;if(Math.abs(z-90)<100&&x<440)continue;house(x,z,20+rnd()*14,18+rnd()*22,22,['#eadcc2','#dce0be','#e6d3b2'][i%3]);}
 for(let i=0;i<12;i++){const angle=i/12*Math.PI*2,x=-330+Math.cos(angle)*124,z=170+Math.sin(angle)*100;box(x,15,z,44,2,16,'#bdb99a',-angle+Math.PI/2);if(i%2===0)tree(x*.96,z*.98,.65);}
 for(let i=0;i<10;i++)house(-390+i%5*29,190+Math.floor(i/5)*34,22,16+i%3*6,21,['#ece0c6','#e0c3a4','#e5d7b7'][i%3]);
 for(let i=0;i<65;i++){let x=440+rnd()*200,z=-450+rnd()*910;tree(x,z,.55+rnd()*.5);}
 for(let i=0;i<11;i++)tree(-380+rnd()*100,85+rnd()*50,.65+rnd()*.35);
 // Small red harbor beacon, granite quay and fishing vessels.
 segment([110,-310],[230,-310],13,5,'#d3c9a9');put(cyl,110,21,-310,5,34,5,'#af6249');put(cyl,110,39,-310,7,4,7,'#f3dec0');boat(156,-287,.8,Math.PI/2);boat(190,-281,.7,Math.PI/2);
 // Angular stainless-steel pickup, parked legally in the illustrated parking lot.
 const truck=new T.Group();const body=new T.Mesh(new T.BoxGeometry(14,5,28),mat('#b8beb9'));body.position.y=6;truck.add(body);const cabGeo=new T.BufferGeometry();cabGeo.setAttribute('position',new T.Float32BufferAttribute([-7,8,-11,7,8,-11,7,13,1,-7,13,1,-7,8,12,7,8,12],3));cabGeo.setIndex([0,1,2,0,2,3,3,2,5,3,5,4,0,3,4,1,5,2]);cabGeo.computeVertexNormals();truck.add(new T.Mesh(cabGeo,new T.MeshStandardMaterial({color:'#c3c8bf',roughness:.3,metalness:.5,side:T.DoubleSide})));const glass=new T.Mesh(new T.BoxGeometry(12,.5,9),mat('#3a5958'));glass.position.set(0,11,-3);glass.rotation.x=-.4;truck.add(glass);for(const x of [-7,7])for(const z of [-8,8]){const wheel=new T.Mesh(new T.CylinderGeometry(3,3,2,10),mat('#37423c'));wheel.rotation.z=Math.PI/2;wheel.position.set(x,3,z);truck.add(wheel);}truck.position.set(194,9,-157);truck.rotation.y=Math.PI/2;root.add(truck);
 // Calm wave lines and channel buoys.
 for(let i=0;i<140;i++){const x=-750+rnd()*1450,z=-550+rnd()*1150;if((x>100)||Math.hypot((x+330)/1.1,z-170)<165||Math.hypot(x+170,z+260)<85)continue;box(x,-.35,z,8+rnd()*16,.15,.6,'#bcd0ba',.15);}
 for(let i=0;i<7;i++){put(cyl,-160+i*40,1,335,1.8,5,1.8,i%2?'#c48154':'#e9d8aa');}
 // Light poles: emissive bulbs at night, no costly per-lamp shadows.
 const bulbMat=new T.MeshStandardMaterial({color:'#ead6a3',emissive:'#ffc46f',emissiveIntensity:0});for(let i=0;i<12;i++){const x=i<6?130+i*26:-430+(i-6)*36,z=i<6?-122:231;box(x,19,z,1.2,25,1.2,'#6d7f68');const bulb=new T.Mesh(new T.SphereGeometry(2.1,6,4),bulbMat);bulb.position.set(x,32,z);root.add(bulb);lights.push(bulb);}
 for(const {g,c,items} of buckets.values()){const mesh=new T.InstancedMesh(g,mat(c),items.length);items.forEach((m,i)=>mesh.setMatrixAt(i,m));mesh.castShadow=true;mesh.receiveShadow=true;root.add(mesh);}
 // Slow gulls add life without leaving walkers stranded on the water.
 const gulls=new T.Group();for(let i=0;i<7;i++){const bird=new T.Group();for(const side of [-1,1]){const wing=new T.Mesh(new T.BoxGeometry(7,.7,2),mat('#f5eedc'));wing.position.x=side*3;wing.rotation.z=side*.3;bird.add(wing);}bird.position.set(-70+i*32,75+i%3*12,20+i*11);gulls.add(bird);}root.add(gulls);
 return {root,animate(t){rotors.forEach((r,i)=>r.rotation.z=-t*.35+i);gulls.position.x=Math.sin(t*.1)*25;gulls.position.z=Math.cos(t*.1)*18;},setMode(mode){waterMaterial.color.set(mode==='day'?'#90b7b1':mode==='sunset'?'#baac89':'#355e65');bulbMat.emissiveIntensity=mode==='night'?2:.05;},count:()=>buckets.size};
}
