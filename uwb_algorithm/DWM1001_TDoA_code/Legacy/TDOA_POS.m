% %% TDOA_POSITION ESTIMATION
% close all
% clear all
% clc
% % Set comunication on COMx
% disp('Initialization acquisition')
% r = serial("COM6",'Baudrate',115200);
% r.Terminator = 'CR';
% fopen(r);
% line = 1;
% text = [];
% % Read String from DWM1001
% while (line <=2)
%     text = fgets(r);
%     disp(text)
%     line = line + 1;
% end
% prompt = 'Set the number of anchor: ';
% num = input(prompt);
% fprintf(r,'%d',num);
% fprintf(r,'%c','\r\n')
% 
% line = 1;
% while (line <=2)
%     text = fgets(r);
%     disp(text)
%     line = line + 1;
% end
% prompt = 'Enter: ';
% answer = input(prompt,'s');
% fprintf(r,'%c',answer)
% 
% line = 1;
% while (line <=2)
%     text = fgets(r);
%     disp(text)
%     line = line + 1;
% end
% pause(1)
% i = 1;
% 
    range_s = 5; %sensor range for each dimension
    range_T = 8; %target range for each dimension
    c = 299792458;    %speed of light
    M = 6;      %number of sensors

    %rmse = zeros(trials,1);

    % centro il sistema in A8 per comodità e lavorare solo con grandezze
    % positive
    Anch_M  = [2.12; 0.0];
    Anch_A3 = [4.24; 0.0]; 
    Anch_A4 = [2.12; 4.24];
    Anch_A5 = [0.0; 4.24];
    Anch_A7 = [0.0; 2.12];
    Anch_A8 = [0.0; 0.0];    

     
    P = [Anch_M Anch_A3 Anch_A4 Anch_A5 Anch_A7 Anch_A8];
   
    p_T = [2.12; 2.12];  %target real position

    cont = 50;    
    data_x = double.empty(cont,0);
    data_y = double.empty(cont,0);
    
    
     ts_master = double.empty(cont,0);
     ts_A3 = double.empty(cont,0);
     ts_A4 = double.empty(cont,0);
     ts_A5 = double.empty(cont,0);
     ts_A7 = double.empty(cont,0);
     ts_A8 = double.empty(cont,0);
     
%     RMSE = double.empty(cont,0);
    
%% extract timestamps
cont = 1;
fopen(r);
pause(1)
while(cont <= 50)
    
    pos =  fscanf(r);
    timestamp = split(pos,' ');

    tm = str2num(timestamp{1,1}) * double(15.65e-12);    %converto in tempo
    t3 = str2num(timestamp{2,1}) * double(15.65e-12);
    t4 = str2num(timestamp{3,1}) * double(15.65e-12);  
    t5 = str2num(timestamp{4,1}) * double(15.65e-12);  
    t7 = str2num(timestamp{5,1}) * double(15.65e-12);  
    t8 = str2num(timestamp{6,1}) * double(15.65e-12);
   
        
    %finding TOAs 
    dummy = repmat(p_T,1,M)-P;

    toa = [tm; t3; t4; t5; t7; t8];
    tdoa = toa-toa(1);
    tdoa(1)=[];

    %% METODO 2D
%     nDim = 2;
%     
%     [~,d] = min(toa);
%     t = toa-toa(d);
%     ijs = 1:M;
%     ijs(d) = [];
%     A = zeros(size(ijs,1), nDim);
%     b = zeros(size(ijs,1),1);
%     iRow = 0;
%     rankA = 0;
%     for i = ijs
%         for j = ijs
%             iRow = iRow + 1;
%             A(iRow,:) = 2*(c*(t(j)-t(d))*(P(:,i)-P(:,d))'-c*(t(i)-t(d))*(P(:,j)-P(:,d))');
%             b(iRow,1) = c*(t(i)-t(d))*(c*c*(t(j)-t(d))^2-P(:,j)'*P(:,j)) ...
%                 +	(c*(t(i)-t(d))-c*(t(j)-t(d)))*P(:,d)'*P(:,d) ...
%                 +	c*(t(j)-t(d))*(P(:,i)'*P(:,i)-c*c*(t(i)-t(d))^2);
%             rankA = rank(A);
%             if(rankA >= nDim)
%                 break;
%             end
%         end
%         if(rankA >= nDim)
%             break;
%         end
%     end
% 
%     x_hat_inv = A\b; %Calculated position of emitter
%     data_x(cont) = x_hat_inv(1);
%     data_y(cont) = x_hat_inv(2);
    
%%    METODO 3D
    p_1 = P(:,1);
    dummy = P(:,2:M)';
    A = 2*[(p_1(1)-dummy(:,1)), (p_1(2)-dummy(:,2)), -c*tdoa];
    b = (c*tdoa).^2 + norm(p_1)^2 - sum((dummy.^2),2);
    x_lin = pinv(A)*b;
%    rmse = norm(p_T-x_lin(1:2))^2;
   
%     data_x(cont) = x_lin(1);
%     data_y(cont) = x_lin(2);
%% METODO NON LINEAR
p_T_0 = [x_lin(1); x_lin(2)];    %initial estimate with some error (penalty term)
d = c*tdoa; 
f = zeros(M-1,1);
del_f = zeros(M-1,2);
for ii=2:M
   f(ii-1)=norm(p_T_0-P(:,ii))-norm(p_T_0-P(:,1)); 
   del_f(ii-1,1) = (p_T_0(1)-P(1,ii))*norm(p_T_0-P(:,ii))^-1 - (p_T_0(1)-P(1,1))*norm(p_T_0-P(:,1))^-1;
   del_f(ii-1,2) = (p_T_0(2)-P(2,ii))*norm(p_T_0-P(:,ii))^-1 - (p_T_0(2)-P(2,1))*norm(p_T_0-P(:,1))^-1;
%    del_f(ii-1,3) = (p_T_0(3)-P(3,ii))*norm(p_T_0-P(:,ii))^-1 - (p_T_0(3)-P(3,1))*norm(p_T_0-P(:,1))^-1;    
end

    x_nonlin = pinv(del_f)*(d-f)+p_T_0;
    data_x(cont) = x_nonlin(1);
    data_y(cont) = x_nonlin(2);
    
    %% DATA_OUT
%     ts_master(cont) = cell2mat(timestamp(2));
%     ts_A3(cont) = cell2mat(timestamp(3));
%     ts_A4(cont) = cell2mat(timestamp(4));
%     ts_A5(cont) = cell2mat(timestamp(5));
%     ts_A7(cont) = cell2mat(timestamp(6));
%     ts_A8(cont) = cell2mat(timestamp(7));
%     
%    RMSE(cont) = rmse;
    
    cont= cont+1;
end

disp('end acquisition');
fclose(r);


   % rmse(1) = norm(p_T-x_lin(1:2))^2;
    
%     figure(1)
%     plot(P(1,:), P(2,:),'o'); hold on;
%     plot(p_T(1), p_T(2),'k*');
%     xlim([-range_T range_T]);ylim([-range_T range_T]);
%     xlabel('x-axis'); ylabel('y-axis'); 
% %     if ~method_flag
%         plot(x_lin(1), x_lin(2),'md','MarkerSize',7.75);  %target estimate with linear solution
% %     else
% %         plot(x_nonlin(1), x_nonlin(2),'ms','MarkerSize',7.75); 
% %     end
%     legend('Sensor Positions', 'Target Position', 'Target Estimation')
%     grid on; 
%     %hold off;
   
    media_x = mean(data_x);
    min_x = min(data_x);
    max_x = max(data_x);
    dev_stdx = std(data_x);
    
    figure(1)
    histogram(data_x,10); 
    
    media_y = mean(data_y);
    min_y = min(data_y);
    max_y = max(data_y);
    dev_stdy = std(data_y);
    
    figure(2)
    histogram(data_y,10);
   
    figure(3)
    plot(P(1,:), P(2,:),'o'); hold on;
    plot(p_T(1), p_T(2),'k*');
    xlim([-1 range_T]);ylim([-1 range_T]);
    xlabel('x-axis'); ylabel('y-axis');
    
    i=1;
    while(i < cont)
     plot(data_x(i), data_y(i),'md','MarkerSize',7.75);   %target estimate with linear solution
    i = i+1;
    end

    
    legend('Anchor Positions', 'Target Position', 'Target Estimation')
    grid on; 
    hold off;

    tm_medio = mean(ts_master);
    t3_medio = mean(ts_A3); 
    t4_medio = mean(ts_A4); 
    t5_medio = mean(ts_A5); 
    t7_medio = mean(ts_A7); 
    t8_medio = mean(ts_A8); 
    
    delta3 = tm_medio - t3_medio;
    delta4 = tm_medio - t4_medio;
    delta5 = tm_medio - t5_medio;
    delta7 = tm_medio - t7_medio;
    delta8 = tm_medio - t8_medio;
    
